# Render Deployment

This project is ready to deploy on Render with two services:

- `waymapper-frontend`: public Streamlit app
- `waymapper-backend`: private FastAPI backend

The configuration lives in [render.yaml](./render.yaml).

## Before you deploy

1. Push this repository to GitHub.
2. Rotate your OpenAI API key if you exposed it in logs earlier.
3. Decide whether you want Render `starter` plans as defined in `render.yaml`.

## Deploy on Render

1. Sign in to Render.
2. Click `New` -> `Blueprint`.
3. Connect your GitHub account if Render asks for it.
4. Select this repository.
5. Keep the Blueprint path as `render.yaml`.
6. Review the two services Render found:
   - `waymapper-backend`
   - `waymapper-frontend`
7. Provide the missing secret for `OPENAI_API_KEY` when Render prompts for unsynced variables.
8. Click `Apply`.

## After deploy

1. Wait for both services to finish deploying.
2. Open the public URL for `waymapper-frontend`.
3. Test a simple prompt first, such as:
   - `plan a 2 day jaipur trip`

## Notes

- The backend is private and is reached by the frontend over Render's internal network.
- The frontend derives the backend URL from Render's internal host and port automatically.
- Slow prompts can still take a while because the planner runs multiple LLM steps.
- If you want lower cost over faster cold starts, you can change the `plan` values in `render.yaml` before deploying.
