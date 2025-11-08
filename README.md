# JobSleuth AI - Production-Ready MVP

JobSleuth AI is a production-quality AI-powered job sourcing platform built with FastAPI (backend), Next.js 15 (frontend), Supabase (database + auth), and Stripe (payments). This MVP includes AI job-fit scoring, resume tools, email digests, and feature flags.

## 🏗️ Architecture

**Monorepo Structure:**
```
jobsleuth-ai/
├── backend/          # FastAPI (Python 3.11)
├── frontend/         # Next.js 15 + App Router (TypeScript)
├── supabase/         # Database migrations & seeds
├── ops/              # Smoke tests & deployment scripts
├── docs/             # Documentation & runbooks
└── .github/          # CI/CD workflows
```

**Tech Stack:**
- **Backend**: FastAPI, Python 3.11, Supabase, OpenAI, Stripe
- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **Database**: Supabase (PostgreSQL) with RLS
- **Auth**: Supabase Auth (magic-link sign-in)
- **Payments**: Stripe with webhook handling
- **AI**: OpenAI GPT-3.5 for scoring & resume tools
- **Email**: Resend or Mailgun for digests
- **Scraping**: Provider APIs (SerpAPI/Zyte) + optional Playwright

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm 8+
- Supabase account
- Stripe account (test mode)

### 1. Clone & Install

```bash
git clone <repository-url>
cd jobsleuth-ai

# Install frontend dependencies
cd frontend
pnpm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Install Playwright browsers (optional, for internal scraping)
playwright install chromium
```

### 2. Environment Setup

Copy `.env.example` to `.env` (root) and `.env.local` (frontend):

```bash
cp .env.example .env
cp .env.example frontend/.env.local
```

**Required Environment Variables:**

**Backend (.env):**
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
PRICE_ID_PRO=price_xxx
PRICE_ID_INVESTOR=price_xxx

# Optional: OpenAI (for AI features)
OPENAI_API_KEY=sk-xxx

# Optional: Email
RESEND_API_KEY=re_xxx

# Backend/Frontend URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_KEY=your_anon_key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Feature Flags (optional)
NEXT_PUBLIC_FEATURE_AI_FIT=true
NEXT_PUBLIC_FEATURE_RESUME_TOOLS=true
NEXT_PUBLIC_FEATURE_DIGESTS=false
NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL=false

# Stripe
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx
NEXT_PUBLIC_STRIPE_PRICE_INVESTOR=price_xxx
```

### 3. Database Setup

Run migrations in your Supabase project:

```bash
# In Supabase SQL Editor, run:
supabase/migrations/20240101000000_initial_schema.sql

# Then run seed data:
supabase/seeds/seed_jobs.sql
```

Or use Supabase CLI:
```bash
supabase db push
supabase db seed
```

### 4. Run Locally

**Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
pnpm dev
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest -v
```

**Test Coverage:**
- ✅ Health endpoint
- ✅ Jobs listing & detail
- ✅ Saved jobs (RLS owner-only)
- ✅ User plan (Bearer token precedence)
- ✅ Stripe webhook (deterministic responses)
- ✅ Scoring service (zero preservation)

### Smoke Tests

```bash
# Start backend, then run:
./ops/smoke-test.sh
```

### Linting

```bash
# Backend
cd backend
ruff check .
ruff format .

# Frontend
cd frontend
pnpm lint
pnpm type-check
```

## 📦 Features

### Core Features ✅

- **Job Listings**: Browse, search, filter jobs with pagination
- **Job Details**: View full job details with salary, location, type
- **Save Jobs**: Save favorite jobs (requires auth)
- **User Accounts**: Magic-link authentication, plan management
- **Stripe Integration**: Free/Pro/Investor plans with webhook handling
- **RLS Security**: Row-level security for user data

### AI Features (Gated by Flags) 🤖

- **AI Fit Scoring**: Match jobs to user profile (0-100 score)
- **Resume Tools**: Generate tailored resume suggestions
- **Cover Letters**: Auto-generate cover letters for jobs
- **Email Digests**: Scheduled job digests via email

### Scraping Features 🕷️

- **Provider-First**: Use SerpAPI/Zyte when available
- **Playwright Fallback**: Internal scraping with rate limiting
- **Normalization**: Convert raw data to schema

## 🎛️ Feature Flags

Control features via environment variables (see `docs/FEATURE_FLAGS.md`):

- `NEXT_PUBLIC_FEATURE_AI_FIT` - AI job fit scoring
- `NEXT_PUBLIC_FEATURE_RESUME_TOOLS` - Resume/cover letter tools
- `NEXT_PUBLIC_FEATURE_DIGESTS` - Email digest subscriptions
- `NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL` - Internal Playwright scraper

All default to `false` when unset.

## 🚢 Deployment

### Frontend (Vercel)

1. Connect repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy (automatic on push to main)

### Backend (Railway)

1. Connect repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy (automatic on push to main)

### Database (Supabase)

Already hosted - just configure connection strings.

### Webhooks

Configure Stripe webhook endpoint:
```
https://your-backend.railway.app/stripe/webhook
```

Events to listen for:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## 📚 API Documentation

**Key Endpoints:**

```
GET  /health                    # Health check
GET  /jobs                      # List jobs (with filters)
GET  /jobs/{id}                 # Get job detail
POST /save-job                  # Save job (requires auth)
GET  /saved-jobs                # Get saved jobs (requires auth)
POST /score                     # Compute job fit score
POST /resume/suggest            # Get resume suggestions
POST /cover-letter              # Generate cover letter
POST /digests/run               # Run digest (admin only)
GET  /users/plan                # Get user plan
POST /stripe/webhook            # Stripe webhook handler
```

See http://localhost:8000/docs for interactive API documentation.

## 🔐 Security

- **RLS**: All user data protected by Row Level Security
- **Auth**: Supabase JWT tokens validated
- **CORS**: Configured for production origins
- **Secrets**: Never committed to source
- **Rate Limiting**: Applied to scraping
- **Input Validation**: Pydantic models
- **CodeQL**: Automated security scanning

## 📊 Database Schema

**Tables:**
- `users` - User profiles with plan info
- `jobs` - Job listings with salary, location
- `saved_jobs` - User's saved jobs (RLS)
- `job_scores` - AI fit scores (RLS)
- `applications` - Application tracking (RLS)
- `digests` - Email digest preferences (RLS)
- `companies` - Company information

See `supabase/migrations/` for full schema.

## 🤝 Contributing

1. Create a feature branch
2. Make changes with tests
3. Run linters: `ruff check`, `pnpm lint`
4. Run tests: `pytest`, `pnpm test`
5. Submit PR

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Email: support@jobsleuth.ai

## 🎯 Roadmap

**Phase 1: MVP** ✅
- Core job listing & search
- User authentication
- Stripe billing
- AI scoring (basic)

**Phase 2: Enhancement** (Next)
- [ ] Advanced search filters
- [ ] Job alerts & notifications
- [ ] Application tracking
- [ ] Team accounts
- [ ] Analytics dashboard

**Phase 3: Scale** (Future)
- [ ] Multi-language support
- [ ] Mobile apps
- [ ] API for partners
- [ ] Custom integrations
- [ ] White-label solution
