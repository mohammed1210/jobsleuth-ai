# Deployment Runbook

## Vercel Frontend

- Root directory: `frontend`
- Install command: `npm ci`
- Build command: `npm run build`
- Required vars: `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_KEY`, `NEXT_PUBLIC_SITE_URL`, Stripe public vars

## Railway Backend

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

## Common Errors

### Cannot find module tailwindcss

Run `npm install` in `frontend` and confirm `tailwindcss`, `postcss`, and `autoprefixer` exist in `frontend/package.json`.

### Conflicting pages/index.js and app/page.tsx

Use App Router only. Remove `frontend/pages` if it appears.

### ModuleNotFoundError: app

Railway is using the wrong start command. With root directory `backend`, use `uvicorn main:app --host 0.0.0.0 --port $PORT`.

### missing send_digest_email

Confirm `backend/services/emailer.py` exports `send_digest_email` and `backend/routes/digests.py` imports it.

### Supabase token localStorage issue

Do not read `localStorage.getItem('supabase_token')`. Use `supabase.auth.getSession()` and pass `session.access_token` in the backend `Authorization` header.

### Debug route not visible

`/debug/routes` returns 404 unless `ENABLE_DEBUG_ROUTES=1`.
