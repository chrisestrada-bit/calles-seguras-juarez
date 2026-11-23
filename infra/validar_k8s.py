"""Valida los manifiestos de infra/k8s/ sin necesitar un clúster.

Comprueba: YAML bien formado, campos obligatorios, coherencia entre objetos (ConfigMap/Secret/PVC referenciados,
selectores de Service contra las etiquetas de los pods, puertos con nombre), sondas de salud del backend apuntando a
/health y que `secret.example.yaml` no contenga secretos reales. Uso:

    python infra/validar_k8s.py            # sale con código 1 si hay errores
"""

import re
import sys
from pathlib import Path

import yaml

DIRECTORIO = Path(__file__).resolve().parent / "k8s"
ARCHIVOS_ESPERADOS = {
    "namespace.yaml", "configmap.yaml", "secret.example.yaml", "postgres-pvc.yaml",
    "postgres-deployment.yaml", "backend-deployment.yaml", "frontend-deployment.yaml", "services.yaml",
}
NAMESPACE = "calles-seguras"
SECRETO_REAL = "calles-seguras-secretos"
VERSION_K8S = "1.31"  # versión mínima objetivo (kind/minikube/k3d actuales)
errores: list[str] = []


def error(mensaje: str) -> None:
    errores.append(mensaje)


def cargar() -> list[tuple[str, dict]]:
    objetos = []
    presentes = {p.name for p in DIRECTORIO.glob("*.yaml")}
    for faltante in sorted(ARCHIVOS_ESPERADOS - presentes):
        error(f"Falta el archivo infra/k8s/{faltante}")
    for ruta in sorted(DIRECTORIO.glob("*.yaml")):
        try:
            for doc in yaml.safe_load_all(ruta.read_text(encoding="utf-8")):
                if doc is None:
                    continue
                if not isinstance(doc, dict) or not {"apiVersion", "kind", "metadata"} <= doc.keys():
                    error(f"{ruta.name}: documento sin apiVersion/kind/metadata")
                    continue
                objetos.append((ruta.name, doc))
        except yaml.YAMLError as exc:
            error(f"{ruta.name}: YAML inválido: {exc}")
    return objetos


def nombre(o: dict) -> str:
    return o["metadata"].get("name", "")


def main() -> int:
    objetos = cargar()
    por_tipo: dict[str, dict[str, dict]] = {}
    for archivo, o in objetos:
        meta = o["metadata"]
        if not meta.get("name"):
            error(f"{archivo}: {o['kind']} sin metadata.name")
        if o["kind"] != "Namespace" and meta.get("namespace") != NAMESPACE:
            error(f"{archivo}: {o['kind']}/{nombre(o)} debe estar en el namespace {NAMESPACE}")
        por_tipo.setdefault(o["kind"], {})[nombre(o)] = o

    configmaps = por_tipo.get("ConfigMap", {})
    pvcs = por_tipo.get("PersistentVolumeClaim", {})
    servicios = por_tipo.get("Service", {})
    deployments = por_tipo.get("Deployment", {})

    # --- secretos: la plantilla es ficticia y no es el Secret que usan los Deployments
    ejemplo = por_tipo.get("Secret", {})
    if SECRETO_REAL in ejemplo:
        error(f"secret.example.yaml no debe llamarse {SECRETO_REAL}: aplicar la carpeta pisaría tus secretos reales")
    claves_secreto: set[str] = set()
    for s in ejemplo.values():
        claves_secreto |= set(s.get("stringData", {})) | set(s.get("data", {}))
        for clave, valor in s.get("stringData", {}).items():
            if clave != "GEOCODING_API_KEY" and not re.search(r"CAMBIA(R)?", str(valor), re.I):
                error(f"secret.example.yaml: {clave} no parece un valor de ejemplo (debe contener CAMBIAR)")
    if not claves_secreto:
        error("secret.example.yaml no documenta ninguna clave")

    # --- Deployments
    etiquetas_pod: dict[str, dict] = {}
    for d in deployments.values():
        spec = d["spec"]
        plantilla = spec["template"]
        etiquetas = plantilla["metadata"]["labels"]
        etiquetas_pod[nombre(d)] = etiquetas
        for k, v in spec["selector"]["matchLabels"].items():
            if etiquetas.get(k) != v:
                error(f"Deployment/{nombre(d)}: el selector {k}={v} no coincide con las etiquetas del pod")
        for c in plantilla["spec"]["containers"] + plantilla["spec"].get("initContainers", []):
            ref = f"Deployment/{nombre(d)}/{c['name']}"
            if not c.get("image") or c["image"].endswith(":latest"):
                error(f"{ref}: usa una imagen con etiqueta fija (no :latest)")
            for e in c.get("envFrom", []):
                cm = e.get("configMapRef", {}).get("name")
                if cm and cm not in configmaps:
                    error(f"{ref}: referencia al ConfigMap inexistente {cm}")
            for e in c.get("env", []):
                vf = e.get("valueFrom", {})
                if "configMapKeyRef" in vf:
                    cm = vf["configMapKeyRef"]
                    claves = (configmaps.get(cm["name"]) or {}).get("data", {})
                    if cm["name"] not in configmaps or cm["key"] not in claves:
                        error(f"{ref}: {e['name']} apunta a {cm['name']}/{cm['key']} que no existe")
                if "secretKeyRef" in vf:
                    sk = vf["secretKeyRef"]
                    if sk["name"] != SECRETO_REAL:
                        error(f"{ref}: {e['name']} debe leer el Secret {SECRETO_REAL}")
                    if sk["key"] not in claves_secreto:
                        error(f"{ref}: la clave {sk['key']} no está documentada en secret.example.yaml")
                if "value" in e and re.search(r"(PASSWORD|SECRET|API_KEY)$", e["name"]) and "$(" not in str(e["value"]):
                    error(f"{ref}: {e['name']} tiene un valor escrito en el manifiesto; debe venir de un Secret")
        for v in plantilla["spec"].get("volumes", []):
            claim = v.get("persistentVolumeClaim", {}).get("claimName")
            if claim and claim not in pvcs:
                error(f"Deployment/{nombre(d)}: PVC inexistente {claim}")

    # --- backend: sondas de salud
    backend = deployments.get("backend")
    if not backend:
        error("Falta Deployment/backend")
    else:
        c = backend["spec"]["template"]["spec"]["containers"][0]
        for sonda in ("livenessProbe", "readinessProbe"):
            http = c.get(sonda, {}).get("httpGet")
            if not http or http.get("path") not in ("/health", "/api/v1/health"):
                error(f"Deployment/backend: {sonda} debe ser httpGet a /health")
        if backend["spec"]["replicas"] != 1:
            error("Deployment/backend: debe tener 1 réplica (el WebSocket en vivo guarda sus conexiones en memoria)")

    # --- Services: selector y puertos
    for s in servicios.values():
        sel = s["spec"]["selector"]
        destino = next((n for n, et in etiquetas_pod.items() if all(et.get(k) == v for k, v in sel.items())), None)
        if destino is None:
            error(f"Service/{nombre(s)}: su selector no coincide con ningún Deployment")
            continue
        puertos_contenedor = {
            p["name"] for c in deployments[destino]["spec"]["template"]["spec"]["containers"] for p in c.get("ports", []) if "name" in p
        }
        for p in s["spec"]["ports"]:
            if isinstance(p["targetPort"], str) and p["targetPort"] not in puertos_contenedor:
                error(f"Service/{nombre(s)}: targetPort {p['targetPort']} no existe en el Deployment/{destino}")
    for esperado in ("postgres", "backend", "frontend"):
        if esperado not in servicios:
            error(f"Falta Service/{esperado}")

    # --- ConfigMap: nada secreto
    for cm in configmaps.values():
        for clave in cm.get("data", {}):
            if re.search(r"(PASSWORD|SECRET_KEY|API_KEY|TOKEN)$", clave):
                error(f"ConfigMap/{nombre(cm)}: {clave} parece un secreto; muévelo al Secret")

    # --- esquema oficial de Kubernetes (offline), si está instalado: pip install kubernetes-validate
    try:
        import kubernetes_validate as kv
    except ImportError:
        print("Aviso: kubernetes-validate no está instalado; se omite la validación contra el esquema oficial.")
    else:
        for archivo, o in objetos:
            try:
                kv.validate(o, VERSION_K8S, strict=True)
            except Exception as exc:  # noqa: BLE001 - kubernetes-validate lanza varios tipos
                error(f"{archivo}: {o['kind']}/{nombre(o)} no cumple el esquema de Kubernetes {VERSION_K8S}: {str(exc)[:160]}")

    for e in errores:
        print(f"ERROR: {e}")
    print(f"{len(objetos)} objetos revisados en {len({a for a, _ in objetos})} archivos: " + ("OK" if not errores else f"{len(errores)} error(es)"))
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
