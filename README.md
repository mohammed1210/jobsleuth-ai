# JobSleuth AI Starter

This repository contains a minimal starter for **JobSleuth AI**, a job‑sourcing platform inspired by PropNexus. It includes a **Next.js** frontend, a **FastAPI** backend, basic **Supabase** authentication, and **Stripe** billing hooks. Use this as a baseline to develop more advanced features.

## Project Structure

```
jobsleuth_starter/
├── frontend/            # Next.js app (app router)
│   ├── app/
│   │   ├── layout.tsx   # Root layout (metadata, theme colors)
│   │   ├── page.tsx     # Home page
│   │   ├── magic-login/page.tsx
│   │   ├── auth/callback/page.tsx
│   │   ├── pricing/page.tsx
│   │   ├── account/page.tsx
│   ├── components/
│   │   ├── HeaderClient.tsx
│   │   └── StripePortalButton.tsx
│   ├── lib/
│   │   └── supabaseClient.ts
│   └── app/globals.css
├── backend/             # FastAPI app
│   ├── main.py
│   └── routes/
│       ├── stripe_routes.py
│       ├── stripe_portal.py
│       └── stripe_webhook.py
├── .github/workflows/   # CI/CD definitions (stubbed)
│   ├── frontend.yml
│   └── backend.yml
├── .env.example
└── README.md
```

## Getting Started

1. **Clone this repo** and create a new branch (e.g. `jobsleuth/bootstrap`).
2. Copy `.env.example` to `.env.local` and fill in the required values:
   - Supabase project URL and keys (create a project at [supabase.com](https://supabase.com)).
   - Stripe public/secret keys and webhook secret.
   - Price IDs for your subscription plans.
   - Frontend and backend URLs for deployed environments.
3. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   cd ../backend
   pip install -r requirements.txt  # create this file as needed
   ```
4. **Run locally**:
   - Frontend: `npm run dev` in `frontend` directory (port 3000).
   - Backend: `uvicorn backend.main:app --reload` (port 8000).
5. **Configure CI/CD**: The `.github/workflows` files contain simple placeholders. Replace them with workflows for Vercel (frontend) and Railway (backend) or your chosen platforms.
6. **Deploy**: Set up projects on Vercel and Railway (or your hosting of choice). Configure environment variables using `.env.local` values.

## Notes

- This starter is intentionally minimal. It demonstrates how to wire together authentication, billing and basic navigation. You should extend it with your own job listing pages, search filters, analytics and custom branding.
- The backend routes for Stripe are stubs; handle subscription events according to your billing model.
- The frontend uses Tailwind CSS; ensure Tailwind is configured in `tailwind.config.js` if you plan to extend styles.
