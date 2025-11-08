# JobSleuth AI MVP - Operations & Testing

This directory contains operational scripts, smoke tests, and end-to-end tests for JobSleuth AI.

## Smoke Tests

Smoke tests verify that the core functionality is working after deployment.

### Backend Smoke Test

```bash
# Test health endpoint
curl -f http://localhost:8000/health

# Test jobs listing
curl -f "http://localhost:8000/jobs?page=1&per_page=10"

# Test job detail (use actual job ID from seed data)
curl -f "http://localhost:8000/jobs/JOB_ID"
```

### Frontend Smoke Test

1. Navigate to `http://localhost:3000`
2. Verify home page loads
3. Click "Browse Jobs" - should navigate to /jobs
4. Verify jobs listing loads
5. Click on a job - should navigate to /jobs/[id]
6. Test Save button (requires auth)
7. Navigate to /pricing - verify pricing page loads
8. Navigate to /account - verify account page loads

## End-to-End Tests

### Authentication Flow

1. Go to /account
2. Click "Sign In with Magic Link"
3. Enter email address
4. Check email for magic link
5. Click link to complete authentication
6. Verify redirect to /account with user info displayed

### Job Saving Flow

1. Sign in to account
2. Navigate to /jobs
3. Click Save on a job card
4. Navigate to /saved
5. Verify saved job appears in list

### Scoring Flow (if AI_FIT enabled)

1. Navigate to a job detail page
2. Verify AI Fit Score panel appears
3. Check that fit score (0-100) and factors are displayed

## Deployment Checklist

- [ ] Backend health endpoint returns 200
- [ ] Database migrations applied successfully
- [ ] Seed data loaded
- [ ] Frontend builds without errors
- [ ] All environment variables configured
- [ ] Stripe webhooks configured
- [ ] Email service tested (if enabled)
- [ ] Feature flags set correctly
- [ ] SSL certificates valid
- [ ] CORS configured properly

## Monitoring

### Key Metrics

- API response times (should be < 500ms for most endpoints)
- Error rates (should be < 1%)
- Database connection pool usage
- Job listing refresh rate
- User sign-up rate
- Conversion rate (free → paid)

### Alerts

Set up alerts for:
- API downtime (health endpoint fails)
- High error rates (> 5% over 5 minutes)
- Database connection issues
- Stripe webhook failures
- Email delivery failures

## Troubleshooting

### Backend won't start

- Check DATABASE_URL is correct
- Verify all required env vars are set
- Check Python dependencies installed
- Review logs for import errors

### Frontend build fails

- Run `pnpm install` to ensure dependencies
- Check NEXT_PUBLIC_* env vars are set
- Verify TypeScript compilation
- Check for syntax errors

### Stripe webhooks not working

- Verify STRIPE_WEBHOOK_SECRET matches Stripe dashboard
- Check webhook endpoint is publicly accessible
- Review Stripe dashboard for delivery attempts
- Verify request signature validation

### Database connection fails

- Check Supabase project is active
- Verify connection string format
- Ensure service role key has correct permissions
- Check network connectivity

## Performance Optimization

### Backend

- Enable database query caching
- Add Redis for session storage
- Implement rate limiting
- Use CDN for static assets
- Enable gzip compression

### Frontend

- Enable Next.js image optimization
- Implement code splitting
- Add service worker for offline support
- Lazy load non-critical components
- Use React.memo for expensive renders

## Security

### Checklist

- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] SQL injection prevention (using ORMs)
- [ ] XSS protection (React default)
- [ ] CSRF protection (SameSite cookies)
- [ ] Secrets not in source code
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Regular dependency updates
- [ ] CodeQL scanning enabled
