Kubernetes manifests for PROVE

Included manifests:
- `backend-deployment.yaml` — backend Deployment
- `backend-service.yaml` — ClusterIP service for backend
- `frontend-deployment.yaml` — frontend Deployment (static site)
- `frontend-service.yaml` — LoadBalancer service for frontend
- `mongo-deployment.yaml` — Mongo Deployment
- `mongo-pvc.yaml` — PVC for Mongo data
- `prove-secrets.yaml` — template Secret (replace values)
- `ingress.yaml` — Ingress routing frontend and API

Apply all manifests:

```bash
kubectl apply -f k8s/
```

Notes
- Replace image names in the Deployment manifests with your registry/image tags.
- Update `prove-secrets.yaml` with secure values and use Kubernetes Secrets or external secret stores in production.
- The `frontend-service` is a LoadBalancer for cloud deployments; change to `ClusterIP` and use an Ingress if needed.
- Consider adding ResourceRequests/limits, PodDisruptionBudgets, and HorizontalPodAutoscalers for production readiness.
