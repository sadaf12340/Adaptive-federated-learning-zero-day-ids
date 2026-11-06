# API Guide

Swagger UI is available at `http://localhost:8000/docs` and OpenAPI JSON is available at `/openapi.json`.

Typical sequence:

1. `POST /api/demo/generate`
2. `POST /api/federated/train`
3. `POST /api/predict`
4. `POST /api/zero-day/evaluate`
5. `GET /api/experiments`

Uploads are limited to CSV files and a configured byte size. Invalid files produce HTTP 400 or 422 responses with field or validation details. No stack trace is exposed by FastAPI application handlers for normal validation failures.
