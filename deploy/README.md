Deployment with Docker Compose (production)

This repo includes a `docker-compose.prod.yml` for production-style deployments.

Prerequisites
- Docker Engine (20+) and Docker Compose

Quick start

1. Create a production env file for the backend at `backend/.env.prod` (copy from `backend/.env.example` and set secure secrets).
2. Build and start the stack:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

3. Backend will be available on port `8000`; frontend served on port `80`.

Notes
- The frontend image builds the Vite app and serves static files via Nginx.
- The `mongo` service persists data to the `mongo_data` volume.
- Customize `backend/.env.prod` and secrets before exposing publicly.
