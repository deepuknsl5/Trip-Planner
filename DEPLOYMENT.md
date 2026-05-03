# Docker Deployment

## Prerequisites

- Docker
- Docker Compose
- An `.env` file in the project root with at least `OPENAI_API_KEY`

You can start from:

```bash
cp .env.example .env
```

## Start the stack

```bash
docker compose up --build
```

## Services

- Frontend: `http://localhost:8501`
- Backend API: `http://localhost:8000`

## Stop the stack

```bash
docker compose down
```

## Notes

- The frontend talks to the backend through `BACKEND_URL=http://backend:8000/plan-trip`.
- Silent local fallback is disabled in Docker by default.
- Backend health is checked before the frontend starts serving requests.
- If `docker compose up --build` fails while downloading Python packages with
  `Connection timed out` or `NameResolutionError`, the issue is Docker network
  resolution rather than the app code. The Docker image now retries package
  installs automatically, but if Docker Desktop DNS is down you should restart
  Docker Desktop and rerun:

```bash
docker compose build --no-cache
docker compose up
```
