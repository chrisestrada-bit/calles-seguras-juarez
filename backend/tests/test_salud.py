"""Sondas de salud: /salud (Docker Compose) y /health (Kubernetes, infra/k8s/backend-deployment.yaml)."""


def test_salud_y_health_responden_ok(client):
    for ruta in ("/salud", "/health"):
        r = client.get(ruta)
        assert r.status_code == 200 and r.json() == {"estado": "ok"}, ruta
