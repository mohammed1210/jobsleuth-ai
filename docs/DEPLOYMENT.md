# JobSleuth AI MVP - Deployment Guide

This guide covers deploying the JobSleuth AI MVP to production.

## Prerequisites

Before deploying, ensure you have:
- [ ] Supabase project created
- [ ] Stripe account with test mode configured
- [ ] Vercel account
- [ ] Railway account (or alternative for backend)
- [ ] Domain name (optional but recommended)

## Step 1: Database Setup (Supabase)

1. Create a Supabase project at https://supabase.com
2. Go to SQL Editor and run migrations:
   ```sql
   -- Run: supabase/migrations/20240101000000_initial_schema.sql
   ```
3. Run seed data:
   ```sql
   -- Run: supabase/seeds/seed_jobs.sql
   ```
4. Note your project credentials:
   - Project URL: `https://your-project.supabase.co`
   - Anon/Public Key: `eyJ...`
   - Service Role Key: `eyJ...` (keep secret!)

## Step 2: Stripe Configuration

1. Log into Stripe Dashboard (https://dashboard.stripe.com)
2. Switch to Test Mode
3. Create Products:
   - **Pro Plan**: $29/month
   - **Investor Plan**: $99/month
4. Note your credentials:
   - Publishable Key: `pk_test_...`
   - Secret Key: `sk_test_...`
   - Price IDs: `price_...` (one for Pro, one for Investor)
5. Set up webhook endpoint (will be configured after backend deployment)

## Step 3: Backend Deployment (Railway)

1. Go to https://railway.app
2. Create new project from GitHub repo
3. Select the `backend` directory as root
4. Configure environment variables:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=eyJ... # anon key
   SUPABASE_SERVICE_ROLE_KEY=eyJ... # service role key
   
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_... # get after configuring webhook
   PRICE_ID_PRO=price_...
   PRICE_ID_INVESTOR=price_...
   
   OPENAI_API_KEY=sk-... # optional, for AI features
   RESEND_API_KEY=re_... # optional, for email
   
   AUTH_SCRAPER_KEY=your-random-secret-key
   BACKEND_URL=https://your-app.railway.app
   FRONTEND_URL=https://your-app.vercel.app
   ```
5. Deploy and note your backend URL

## Step 4: Configure Stripe Webhook

1. Back in Stripe Dashboard, go to Webhooks
2. Add endpoint: `https://your-backend.railway.app/stripe/webhook`
3. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy the Webhook Signing Secret (starts with `whsec_`)
5. Update Railway environment variable: `STRIPE_WEBHOOK_SECRET=whsec_...`
6. Restart backend service

## Step 5: Frontend Deployment (Vercel)

1. Go to https://vercel.com
2. Import project from GitHub
3. Configure:
   - Root Directory: `frontend`
   - Framework Preset: Next.js
   - Build Command: `pnpm build`
   - Install Command: `pnpm install`
4. Configure environment variables:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_KEY=eyJ... # anon key
   NEXT_PUBLIC_BACKEND_URL=https://your-backend.railway.app
   
   NEXT_PUBLIC_STRIPE_PRICE_PRO=price_...
   NEXT_PUBLIC_STRIPE_PRICE_INVESTOR=price_...
   
   # Feature Flags (optional)
   NEXT_PUBLIC_FEATURE_AI_FIT=true
   NEXT_PUBLIC_FEATURE_RESUME_TOOLS=true
   NEXT_PUBLIC_FEATURE_DIGESTS=false
   NEXT_PUBLIC_FEATURE_SCRAPE_INTERNAL=false
   ```
5. Deploy and note your frontend URL

## Step 6: Update Backend with Frontend URL

1. In Railway, update `FRONTEND_URL` to your Vercel deployment URL
2. Restart backend service

## Step 7: Configure Supabase Auth

1. In Supabase Dashboard, go to Authentication > URL Configuration
2. Add Vercel URL to:
   - Site URL: `https://your-app.vercel.app`
   - Redirect URLs: `https://your-app.vercel.app/auth/callback`
3. Enable Email Provider in Authentication > Providers
4. Configure email templates if desired

## Step 8: Test Deployment

### Smoke Tests

1. **Backend Health Check**
   ```bash
   curl https://your-backend.railway.app/health
   # Should return: {"ok": true}
   ```

2. **Frontend Pages**
   - Visit https://your-app.vercel.app
   - Navigate to /jobs
   - Navigate to /pricing
   - Navigate to /account

3. **Authentication Flow**
   - Go to /account
   - Click "Sign In with Magic Link"
   - Enter email
   - Check email for magic link
   - Complete sign-in

4. **Job Operations**
   - Browse jobs at /jobs
   - Click on a job to view details
   - Save a job (requires auth)
   - View saved jobs at /saved

5. **Stripe Integration**
   - Go to /pricing
   - Click "Upgrade to Pro"
   - Complete checkout (use test card: 4242 4242 4242 4242)
   - Verify plan upgraded in /account

## Step 9: Production Checklist

Before going live:

- [ ] Update Stripe to Production mode
- [ ] Use production Stripe keys
- [ ] Configure custom domain
- [ ] Set up SSL (automatic on Vercel/Railway)
- [ ] Configure email service (Resend/Mailgun)
- [ ] Set OpenAI API key for AI features
- [ ] Review and adjust feature flags
- [ ] Set up monitoring/alerts
- [ ] Configure backups for Supabase
- [ ] Review RLS policies
- [ ] Test all user flows end-to-end
- [ ] Load test critical endpoints
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure analytics (optional)

## Step 10: Monitoring

### Key Metrics to Monitor

1. **Backend Health**
   - API response times
   - Error rates
   - Database connection pool

2. **User Metrics**
   - Sign-ups
   - Active users
   - Conversion rates (free → paid)

3. **Business Metrics**
   - Jobs viewed
   - Jobs saved
   - Stripe subscriptions
   - Revenue

### Alerts to Set Up

- Backend downtime (health check fails)
- High error rates (> 5%)
- Database connection issues
- Stripe webhook failures
- Email delivery failures

## Troubleshooting

### Backend Issues

**Problem**: Health check fails
- Check Railway logs
- Verify all environment variables set
- Check Supabase connection

**Problem**: Stripe webhooks not working
- Verify webhook URL is correct
- Check webhook secret matches
- Review Stripe dashboard for delivery attempts

### Frontend Issues

**Problem**: Build fails on Vercel
- Check build logs
- Verify all NEXT_PUBLIC_ variables set
- Check for TypeScript errors

**Problem**: Authentication not working
- Verify Supabase redirect URLs
- Check email provider configured
- Review Supabase auth logs

## Support

For issues:
1. Check logs in Railway/Vercel
2. Review GitHub Issues
3. Consult documentation in /docs
4. Contact support@jobsleuth.ai

## Next Steps

After successful deployment:
1. Announce launch
2. Monitor metrics closely
3. Gather user feedback
4. Plan Phase 2 features
5. Scale infrastructure as needed

---

**Congratulations!** Your JobSleuth AI MVP is now live! 🎉
