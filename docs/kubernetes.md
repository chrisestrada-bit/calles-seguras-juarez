# Despliegue en Kubernetes (Punto extra 4.1)

Manifiestos en [`infra/k8s/`](../infra/k8s/) para un clúster local (`kind`, `minikube` o `k3d`) o en la nube.
`docker-compose.yml` **no cambia**: sigue siendo el Plan B local (`docker compose up --build`, menos de 3 minutos).

## Qué se despliega

| Archivo | Objeto | Notas |
|---------|--------|-------|
| `namespace.yaml` | `Namespace calles-seguras` | Todo vive aquí; se limpia con un solo comando. |
| `configmap.yaml` | `ConfigMap calles-seguras-config` | Configuración **no secreta** (CORS, zona horaria, URLs de proveedores). |
| `secret.example.yaml` | `Secret calles-seguras-secretos-ejemplo` | Plantilla con valores ficticios. **No** es el Secret que se usa (ver abajo). |
| `postgres-pvc.yaml` | 2 × `PersistentVolumeClaim` | Datos de PostgreSQL (2 GiB) y fotografías de reportes (1 GiB). |
| `postgres-deployment.yaml` | `Deployment postgres` | 1 réplica, `Recreate`, sondas con `pg_isready`. |
| `backend-deployment.yaml` | `Deployment backend` | Migra, siembra (si `RUN_SEED=true`) y arranca la API. `startupProbe`, `livenessProbe` y `readinessProbe` apuntan a **`/health`**. |
| `frontend-deployment.yaml` | `Deployment frontend` | Nginx con el build de React, 2 réplicas. |
| `services.yaml` | 3 × `Service` (ClusterIP) | `postgres:5432`, `backend:8000`, `frontend:80`. |

Dos decisiones que conviene conocer:

* **Backend con 1 réplica.** El canal WebSocket de encharcamientos en vivo guarda sus conexiones en la memoria del proceso. Con
  varias réplicas haría falta un bus compartido (p. ej. Redis Pub/Sub).
* **El Secret real nunca está en el repositorio.** `secret.example.yaml` se llama `calles-seguras-secretos-ejemplo`, un nombre
  que ningún Deployment lee, para que `kubectl apply -f infra/k8s/` jamás pise tus secretos reales con valores de ejemplo.

## Requisitos

`docker`, `kubectl` y uno de: [`kind`](https://kind.sigs.k8s.io/), [`minikube`](https://minikube.sigs.k8s.io/) o [`k3d`](https://k3d.io/).
Todos los comandos se ejecutan desde la **raíz del repositorio**.

## 1. Crear el clúster

```bash
# kind
kind create cluster --name calles-seguras

# minikube
minikube start -p calles-seguras

# k3d
k3d cluster create calles-seguras
```

## 2. Construir las imágenes y cargarlas al clúster

El frontend incrusta la URL de la API **al compilar**. Con `port-forward` (paso 4) el navegador llega a la API en
`http://localhost:8000`, que es el valor de abajo. Si la expones con otra URL (Ingress, LoadBalancer), cámbiala aquí **y**
`FRONTEND_URL` en `configmap.yaml` (debe ser exactamente el origen del navegador).

```bash
docker build -f backend/Dockerfile -t calles-seguras-backend:local .
docker build -f frontend/Dockerfile --build-arg VITE_API_BASE_URL=http://localhost:8000 -t calles-seguras-frontend:local frontend
```

```bash
# kind
kind load docker-image calles-seguras-backend:local calles-seguras-frontend:local --name calles-seguras

# minikube
minikube -p calles-seguras image load calles-seguras-backend:local
minikube -p calles-seguras image load calles-seguras-frontend:local

# k3d
k3d image import calles-seguras-backend:local calles-seguras-frontend:local -c calles-seguras
```

## 3. Desplegar

El orden importa: primero el *namespace*, luego el Secret y después todo lo demás.

```bash
kubectl apply -f infra/k8s/namespace.yaml

# Secreto real con valores propios (no se escribe ningún archivo con secretos):
kubectl -n calles-seguras create secret generic calles-seguras-secretos \
  --from-literal=POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')" \
  --from-literal=JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  --from-literal=SEED_PASSWORD='Juarez2026' \
  --from-literal=GEOCODING_API_KEY=''

kubectl apply -f infra/k8s/

kubectl -n calles-seguras rollout status deployment/postgres --timeout=180s
kubectl -n calles-seguras rollout status deployment/backend --timeout=300s
kubectl -n calles-seguras rollout status deployment/frontend --timeout=120s
kubectl -n calles-seguras get pods
```

Notas: `POSTGRES_PASSWORD` debe ser apta para una URL (usa `token_urlsafe`, sin `@ : / ? # %`). `SEED_PASSWORD` es la
contraseña de las cuentas de prueba (mínimo 8 caracteres con letras y números). `JWT_SECRET_KEY` debe tener al menos 32
caracteres: con `APP_ENV=production` el backend no arranca con una clave de ejemplo. La primera vez el backend tarda
1–2 minutos porque ejecuta migraciones y la semilla (la `startupProbe` le da margen).

## 4. Acceder

Abre **dos** terminales (o ejecuta los comandos en segundo plano):

```bash
kubectl -n calles-seguras port-forward svc/backend 8000:8000
kubectl -n calles-seguras port-forward svc/frontend 5173:80
```

* Aplicación: <http://localhost:5173>
* API: <http://localhost:8000/salud> (y `/health`). La documentación `/docs` está **desactivada** porque `APP_ENV=production`;
  para verla, cambia `APP_ENV` a `development` en `configmap.yaml` y reinicia el backend.
* Cuentas de prueba (contraseña = `SEED_PASSWORD`): `coordinador@ejemplo.mx`, `moderador@ejemplo.mx`, `enlace@ejemplo.mx`,
  `ciudadano01@ejemplo.mx`.

Comprobaciones útiles:

```bash
kubectl -n calles-seguras logs deployment/backend --tail=50
kubectl -n calles-seguras describe pod -l app.kubernetes.io/name=backend
kubectl -n calles-seguras exec deployment/postgres -- psql -U csj_app -d calles_seguras -c "select count(*) from reportes;"
```

## 5. Actualizar

```bash
# Tras cambiar código: reconstruye y vuelve a cargar la imagen (pasos 2) y reinicia el Deployment.
kubectl -n calles-seguras rollout restart deployment/backend
# Tras cambiar configmap.yaml:
kubectl apply -f infra/k8s/configmap.yaml && kubectl -n calles-seguras rollout restart deployment/backend
```

## 6. Limpiar

```bash
# Borra TODO el despliegue, incluidos los volúmenes (se pierden los datos de prueba):
kubectl delete namespace calles-seguras

# Y, si quieres, el clúster:
kind delete cluster --name calles-seguras        # kind
minikube delete -p calles-seguras                # minikube
k3d cluster delete calles-seguras                # k3d
```

## Validación sin clúster

```bash
pip install pyyaml kubernetes-validate
python infra/validar_k8s.py
```

El script comprueba que el YAML esté bien formado, que cada objeto cumpla el **esquema oficial de Kubernetes 1.31** (modo
estricto, sin conexión), que los ConfigMap/Secret/PVC referenciados existan, que los selectores de los `Service` coincidan con
las etiquetas de los pods, que las sondas del backend apunten a `/health`, y que ni el ConfigMap ni el Deployment contengan
secretos escritos. Corre también en CI (job `infraestructura`). Si tienes un clúster, además puedes usar
`kubectl apply --dry-run=server -f infra/k8s/`.

> `kubectl apply --dry-run=client` **necesita un clúster accesible** para descubrir los tipos de la API; sin él falla con
> `connection refused`. Por eso la validación de CI usa el script anterior.

## Producción

Esto es un despliegue de demostración. Antes de usarlo con datos reales: fija `RUN_SEED: "false"`, usa un PostgreSQL
administrado (o un operador con respaldos), un Ingress con TLS, un registro de imágenes con etiquetas inmutables (en lugar de
`:local`), un servidor OSRM propio y un mosaico de mapas con SLA (ver `docs/arquitectura.md` §10 y §12.6).
