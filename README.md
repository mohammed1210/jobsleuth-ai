# JobSleuth AI

**AI-powered job sourcing platform** built with FastAPI (backend), Next.js 15 (frontend), Supabase (database + auth), and Stripe (billing).

JobSleuth AI helps job seekers discover, analyze, and land their dream jobs using AI-powered matching, resume tools, and personalized job alerts.

---

## 🚀 Features

- **Job Search & Browse**: Search thousands of job listings with advanced filters
- **AI Job Fit Scoring**: Get personalized match scores based on your resume and preferences
- **Resume Tools**: AI-powered resume enhancement and cover letter generation
- **Saved Jobs**: Bookmark jobs for later review
- **Email Digests**: Receive curated job listings directly to your inbox
- **Stripe Integration**: Freemium model with Pro and Investor subscription tiers
- **Magic Link Auth**: Passwordless authentication via Supabase
- **Row-Level Security**: Secure data access with Supabase RLS policies

---

## 📁 Project Structure

```
jobsleuth-ai/
├── backend/                 # FastAPI backend (Python 3.11+)
│   ├── lib/                # Core utilities (auth, settings, supabase)
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic (scoring, email)
│   ├── scrapers/           # Job scraping utilities
│   └── tests/              # Pytest test suite
├── frontend/               # Next.js 15 frontend (TypeScript)
│   ├── app/                # App router pages
│   ├── components/         # React components
│   └── lib/                # Utilities (flags, supabase client)
├── supabase/               # Database migrations and seeds
│   └── migrations/         # SQL migration files
├── .github/workflows/      # CI/CD pipelines
├── docs/                   # Documentation
│   ├── FEATURE_FLAGS.md   # Feature flag documentation
│   └── RUNBOOK.md         # Deployment runbook
└── ops/                    # Operations and smoke tests
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth (JWT)
- **AI/ML**: OpenAI GPT-3.5, scikit-learn
- **Email**: Resend API
- **Payments**: Stripe
- **Scraping**: Playwright, SerpAPI
- **Testing**: Pytest, httpx

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Auth**: Supabase Auth Helpers
- **Payments**: Stripe.js

### Infrastructure
- **Backend Hosting**: Railway
- **Frontend Hosting**: Vercel
- **Database**: Supabase
- **CI/CD**: GitHub Actions
- **Linting**: Ruff (Python), ESLint (TypeScript)

---

## 🏁 Getting Started

### Prerequisites

- **Node.js 20+** and pnpm
- **Python 3.11+** and pip
- **Supabase account** (free tier available)
- **Stripe account** (test mode)

### 1. Clone the Repository

```bash
git clone https://github.com/mohammed1210/jobsleuth-ai.git
cd jobsleuth-ai
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env.local
```

Required environment variables:

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
PRICE_ID_PRO=price_...
PRICE_ID_INVESTOR=price_...

# OpenAI (optional, for AI features)
OPENAI_API_KEY=sk-...

# Email (optional, for digests)
RESEND_API_KEY=re_...

# Frontend
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 3. Set Up Supabase Database

Run the migrations to create tables and seed data:

```bash
# Option 1: Using Supabase CLI (recommended)
supabase db push

# Option 2: Manually in Supabase Dashboard
# Copy and run the SQL from supabase/migrations/ in order
```

### 4. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
pnpm install
```

### 5. Run Development Servers

**Backend** (runs on http://localhost:8000):
```bash
cd backend
uvicorn main:app --reload
```

**Frontend** (runs on http://localhost:3000):
```bash
cd frontend
pnpm dev
```

Visit http://localhost:3000 to see the application!

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
pnpm test  # If tests are configured
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
pnpm format:check
```

---

## 📦 Deployment

### Backend (Railway)

1. Create a new Railway project
2. Connect your GitHub repository
3. Set the root directory to `backend/`
4. Add environment variables in Railway dashboard
5. Deploy!

Railway will automatically detect the `Dockerfile` and build your backend.

### Frontend (Vercel)

1. Import your GitHub repository in Vercel
2. Set the root directory to `frontend/`
3. Add environment variables in Vercel dashboard
4. Deploy!

Vercel will automatically detect Next.js and configure the build.

### Database (Supabase)

1. Create a Supabase project
2. Run migrations via Supabase CLI or dashboard
3. Configure RLS policies (already in migrations)
4. Update environment variables with Supabase URLs and keys

---

## 🎯 Feature Flags

JobSleuth AI uses feature flags to control rollout of new features. See [docs/FEATURE_FLAGS.md](docs/FEATURE_FLAGS.md) for details.

Available flags:
- `NEXT_PUBLIC_FEATURE_AI_FIT` - AI job fit scoring
- `NEXT_PUBLIC_FEATURE_RESUME_TOOLS` - Resume enhancement tools
- `NEXT_PUBLIC_FEATURE_DIGESTS` - Email digest subscriptions
- `NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL` - Internal Playwright scraping

---

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

Key endpoints:
- `GET /health` - Health check
- `GET /jobs` - List jobs with filters
- `GET /jobs/{id}` - Get job details
- `POST /save-job` - Save a job (requires auth)
- `GET /saved-jobs` - Get saved jobs (requires auth)
- `POST /score` - Calculate job fit score
- `GET /users/plan` - Get user's subscription plan

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- **Python**: Follow PEP 8, use Ruff for linting
- **TypeScript**: Follow Airbnb style guide, use ESLint
- **Commits**: Use conventional commit messages
- **Tests**: Write tests for new features

---

## 📖 Documentation

- [Feature Flags](docs/FEATURE_FLAGS.md) - Feature flag configuration
- [Runbook](docs/RUNBOOK.md) - Deployment and operations guide
- [API Docs](http://localhost:8000/docs) - Interactive API documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Next.js](https://nextjs.org/)
- Database by [Supabase](https://supabase.com/)
- Payments by [Stripe](https://stripe.com/)
- AI by [OpenAI](https://openai.com/)

---

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Email: support@jobsleuth.ai (if configured)

---

**Built with ❤️ for job seekers everywhere**
