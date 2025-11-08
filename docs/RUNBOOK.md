# JobSleuth AI Operations Runbook

This runbook provides step-by-step instructions for deploying, managing, and troubleshooting JobSleuth AI in production.

---

## Table of Contents

1. [Deployment](#deployment)
2. [Database Management](#database-management)
3. [Feature Flag Management](#feature-flag-management)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Common Issues](#common-issues)
6. [Maintenance Tasks](#maintenance-tasks)

---

## Deployment

### Initial Setup

#### 1. Supabase (Database)

1. **Create Supabase Project**
   - Visit [supabase.com](https://supabase.com)
   - Create a new project (select region close to your users)
   - Note the project URL and keys

2. **Run Migrations**
   ```bash
   # Install Supabase CLI
   npm install -g supabase

   # Login
   supabase login

   # Link project
   supabase link --project-ref your-project-ref

   # Run migrations
   supabase db push
   ```

3. **Verify RLS Policies**
   - Check Supabase Dashboard → Authentication → Policies
   - Ensure RLS is enabled on `users`, `saved_jobs`, `job_scores`, `applications`, `digests`
   - Test with sample user to verify permissions

#### 2. Backend (Railway)

1. **Create Railway Project**
   - Visit [railway.app](https://railway.app)
   - New Project → Deploy from GitHub repo
   - Select `mohammed1210/jobsleuth-ai`

2. **Configure Build Settings**
   - Root Directory: `backend`
   - Build Command: (auto-detected from Dockerfile)
   - Start Command: (auto-detected)

3. **Add Environment Variables**
   ```bash
   # Required
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   PRICE_ID_PRO=price_...
   PRICE_ID_INVESTOR=price_...

   # Optional but recommended
   OPENAI_API_KEY=sk-...
   RESEND_API_KEY=re_...
   AUTH_SCRAPER_KEY=generate-secure-random-key

   # Feature flags
   FEATURE_AI_FIT=true
   FEATURE_RESUME_TOOLS=true
   FEATURE_DIGESTS=true
   FEATURE_SCRAPE_INTERNAL=false
   ```

4. **Deploy**
   - Railway will auto-deploy on commit to main
   - Note the generated URL (e.g., `https://your-app.up.railway.app`)

5. **Configure Stripe Webhook**
   - In Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://your-app.up.railway.app/stripe/webhook`
   - Select events: `checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`
   - Copy webhook secret to Railway env vars

#### 3. Frontend (Vercel)

1. **Import Project**
   - Visit [vercel.com](https://vercel.com)
   - New Project → Import Git Repository
   - Select `mohammed1210/jobsleuth-ai`

2. **Configure Build Settings**
   - Framework Preset: Next.js
   - Root Directory: `frontend`
   - Build Command: `pnpm build`
   - Output Directory: `.next` (auto-detected)

3. **Add Environment Variables**
   ```bash
   NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
   NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

   # Feature flags
   NEXT_PUBLIC_FEATURE_AI_FIT=true
   NEXT_PUBLIC_FEATURE_RESUME_TOOLS=true
   NEXT_PUBLIC_FEATURE_DIGESTS=true
   NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL=false
   ```

4. **Deploy**
   - Vercel will auto-deploy on commit to main
   - Configure custom domain (optional)

---

## Database Management

### Running New Migrations

```bash
# Create new migration
supabase migration new your_migration_name

# Edit the migration file in supabase/migrations/

# Test migration locally
supabase db reset

# Apply to production
supabase db push --db-url "your-production-db-url"
```

### Backups

Supabase automatically backs up your database. To create manual backup:

1. Supabase Dashboard → Database → Backups
2. Click "Create Backup"
3. Download if needed

### Data Seeding

To add more sample jobs:

```sql
-- Run in Supabase SQL Editor
INSERT INTO jobs (source, title, company, location, salary_min, salary_max, type, url)
VALUES ('manual', 'Job Title', 'Company Name', 'Location', 100000, 150000, 'Full-time', 'https://...');
```

---

## Feature Flag Management

### Enabling a Feature

1. **Update Environment Variables**
   - Railway: Dashboard → Variables → Add
   - Vercel: Dashboard → Settings → Environment Variables

2. **Redeploy if Necessary**
   - Railway: Auto-deploys on env change
   - Vercel: May need to trigger redeploy

3. **Verify Feature**
   - Test in production
   - Monitor error logs

### Rolling Back a Feature

Set the feature flag to `false` and redeploy:

```bash
# Example: Disable AI fit scoring
NEXT_PUBLIC_FEATURE_AI_FIT=false
FEATURE_AI_FIT=false
```

---

## Monitoring & Alerts

### Health Checks

**Backend Health:**
```bash
curl https://your-app.up.railway.app/health
# Should return: {"ok": true}
```

**Frontend Health:**
```bash
curl https://your-domain.vercel.app/
# Should return 200 OK
```

### Log Monitoring

**Railway Logs:**
- Dashboard → Deployments → View Logs
- Look for errors, 500 responses

**Vercel Logs:**
- Dashboard → Logs
- Filter by time/status code

### Key Metrics to Monitor

1. **API Response Times**
   - Target: < 500ms for /jobs
   - Target: < 2s for /score

2. **Error Rates**
   - Target: < 1% 5xx errors
   - Alert if > 5%

3. **Database Connections**
   - Monitor Supabase connection pool
   - Scale up if near limit

4. **Stripe Webhooks**
   - Check Stripe Dashboard → Webhooks
   - Ensure events are being delivered

---

## Common Issues

### Issue: Stripe Webhook Failing

**Symptoms:**
- 400 errors in webhook endpoint
- Subscriptions not updating

**Solution:**
1. Verify webhook secret matches Stripe dashboard
2. Check Railway logs for detailed error
3. Test webhook with Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:8000/stripe/webhook
   stripe trigger checkout.session.completed
   ```

### Issue: Jobs Not Loading

**Symptoms:**
- Empty job listings
- 500 error on /jobs endpoint

**Solution:**
1. Check Supabase connection:
   ```bash
   curl https://your-app.up.railway.app/health
   ```
2. Verify database has jobs:
   ```sql
   SELECT COUNT(*) FROM jobs;
   ```
3. Check RLS policies (may be blocking public access)

### Issue: AI Features Not Working

**Symptoms:**
- Scoring returns basic heuristics only
- Resume tools show fallback

**Solution:**
1. Verify `OPENAI_API_KEY` is set in Railway
2. Check OpenAI API quota/billing
3. Review Railway logs for OpenAI errors

### Issue: Email Digests Not Sending

**Symptoms:**
- `/digests/run` endpoint fails
- No emails received

**Solution:**
1. Verify `RESEND_API_KEY` is set
2. Check Resend dashboard for delivery status
3. Verify `AUTH_SCRAPER_KEY` matches when calling endpoint

---

## Maintenance Tasks

### Weekly

- [ ] Review error logs in Railway and Vercel
- [ ] Check Supabase database size (free tier: 500MB)
- [ ] Verify Stripe webhook delivery rate

### Monthly

- [ ] Review feature flag usage
- [ ] Update dependencies (backend + frontend)
- [ ] Review and optimize slow queries
- [ ] Check OpenAI/Resend/Stripe usage

### Quarterly

- [ ] Database backup download
- [ ] Security audit (npm audit, ruff check)
- [ ] Performance optimization
- [ ] Update documentation

---

## Emergency Contacts

- **Repository**: https://github.com/mohammed1210/jobsleuth-ai
- **Supabase Support**: https://supabase.com/support
- **Railway Support**: https://railway.app/help
- **Vercel Support**: https://vercel.com/support
- **Stripe Support**: https://support.stripe.com

---

## Rollback Procedure

If a deployment breaks production:

1. **Immediate Actions**
   - Vercel: Dashboard → Deployments → Previous Deployment → "Promote to Production"
   - Railway: Dashboard → Deployments → Previous Deployment → "Redeploy"

2. **Verify Rollback**
   - Test health endpoints
   - Verify critical flows (job search, save, scoring)

3. **Post-Mortem**
   - Identify root cause
   - Create issue in GitHub
   - Update runbook with lessons learned

---

**Last Updated**: 2025-11-08
**Version**: 1.0.0
