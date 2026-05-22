# JobSleuth AI

JobSleuth AI is a FastAPI + Next.js App Router MVP for AI-assisted job search, saved opportunities, Stripe subscriptions, and Supabase magic-link auth.

## Stack

- Backend: FastAPI, Supabase, Stripe, OpenAI fallback routes, SMTP digest stub
- Frontend: Next.js App Router, TypeScript, Tailwind, Supabase Auth
- Database: Supabase Postgres with RLS
- Payments: Stripe Checkout, billing portal, webhook route

## Local Setup

```bash
cp .env.example .env

cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 for the frontend and http://localhost:8000/docs for the API docs.

## Environment

Use `.env.example` as the contract. The frontend needs `NEXT_PUBLIC_BACKEND_URL`, Supabase public vars, Stripe public price IDs, and `NEXT_PUBLIC_SITE_URL`. The backend needs Supabase service vars, Stripe secret vars, `FRONTEND_URL`, optional `ALLOWED_ORIGINS`, optional `OPENAI_API_KEY`, and optional SMTP email vars.

Missing OpenAI or email configuration is safe: AI routes return deterministic fallback output and digest email returns a no-op response.

## Vercel Frontend Setup

- Root directory: `frontend`
- Build command: `npm run build`
- Install command: `npm ci`
- Required vars: `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_KEY`, `NEXT_PUBLIC_SITE_URL`, Stripe public vars

## Railway Backend Setup

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

Do not use `uvicorn app.main:app`; the backend entrypoint is `backend/main.py` and Railway root should be `backend`.

## Supabase Setup

1. Create a Supabase project.
2. Run `supabase/schema.sql` in the SQL editor.
3. Add the anon key to frontend env and the service role key to backend env.
4. Enable magic-link auth and add your Vercel/local callback URL: `/auth/callback`.

## Stripe Setup

1. Create Pro and Career Plus recurring prices.
2. Set `NEXT_PUBLIC_STRIPE_PRICE_PRO` and `NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS`.
3. Set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` on Railway.
4. Configure webhook endpoint: `https://your-backend.railway.app/stripe/webhook`.

## Testing Checklist

```bash
cd backend
pip install -r requirements.txt
python -c "from main import app; print(app)"
```

```bash
cd frontend
npm install
npm run build
```

Also verify:

- `GET /health` returns `{ "status": "ok" }`
- `GET /config` returns safe configuration status
- `GET /debug/routes` is only available when `ENABLE_DEBUG_ROUTES=1`
- `/saved` uses `supabase.auth.getSession()` and sends `session.access_token`
- There is no `frontend/pages` directory
