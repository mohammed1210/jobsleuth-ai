-- JobSleuth AI - Initial Schema Migration
-- This migration creates all core tables for the JobSleuth AI application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    email TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'free' NOT NULL,
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    website TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    external_id TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_text TEXT,
    type TEXT,
    url TEXT UNIQUE NOT NULL,
    posted_at TIMESTAMPTZ,
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'applied' NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Saved jobs table
CREATE TABLE IF NOT EXISTS saved_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, job_id)
);

-- Job scores table (AI fit scoring)
CREATE TABLE IF NOT EXISTS job_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fit_score NUMERIC(5,2) NOT NULL CHECK (fit_score >= 0 AND fit_score <= 100),
    factors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(job_id, user_id)
);

-- Digests table (email digest settings)
CREATE TABLE IF NOT EXISTS digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cadence TEXT DEFAULT 'weekly' NOT NULL CHECK (cadence IN ('daily', 'weekly', 'monthly')),
    last_sent TIMESTAMPTZ,
    filters JSONB,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON saved_jobs(job_id);

CREATE INDEX IF NOT EXISTS idx_job_scores_user_id ON job_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_job_id ON job_scores(job_id);
CREATE INDEX IF NOT EXISTS idx_job_scores_fit_score ON job_scores(fit_score DESC);

CREATE INDEX IF NOT EXISTS idx_digests_user_id ON digests(user_id);

-- Create unique constraint on jobs (source, external_id) where external_id is not null
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_source_external_id 
    ON jobs(source, external_id) 
    WHERE external_id IS NOT NULL;

-- Add or update plan constraint on users table
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_plan_check;
ALTER TABLE users ADD CONSTRAINT users_plan_check 
    CHECK (plan IN ('free', 'pro', 'investor'));

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE digests ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
-- Users can select and update their own record
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON users;
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for applications table
DROP POLICY IF EXISTS "Users can view own applications" ON applications;
CREATE POLICY "Users can view own applications" ON applications
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own applications" ON applications;
CREATE POLICY "Users can create own applications" ON applications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own applications" ON applications;
CREATE POLICY "Users can update own applications" ON applications
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own applications" ON applications;
CREATE POLICY "Users can delete own applications" ON applications
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for saved_jobs table
DROP POLICY IF EXISTS "Users can view own saved jobs" ON saved_jobs;
CREATE POLICY "Users can view own saved jobs" ON saved_jobs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can save jobs" ON saved_jobs;
CREATE POLICY "Users can save jobs" ON saved_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own saved jobs" ON saved_jobs;
CREATE POLICY "Users can delete own saved jobs" ON saved_jobs
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for job_scores table
DROP POLICY IF EXISTS "Users can view own job scores" ON job_scores;
CREATE POLICY "Users can view own job scores" ON job_scores
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own job scores" ON job_scores;
CREATE POLICY "Users can create own job scores" ON job_scores
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own job scores" ON job_scores;
CREATE POLICY "Users can update own job scores" ON job_scores
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for digests table
DROP POLICY IF EXISTS "Users can view own digest settings" ON digests;
CREATE POLICY "Users can view own digest settings" ON digests
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own digest settings" ON digests;
CREATE POLICY "Users can manage own digest settings" ON digests
    FOR ALL USING (auth.uid() = user_id);

-- Jobs table is publicly readable (no RLS needed for SELECT)
-- This allows anonymous users to browse jobs
DROP POLICY IF EXISTS "Jobs are publicly readable" ON jobs;
CREATE POLICY "Jobs are publicly readable" ON jobs
    FOR SELECT USING (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for applications table
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
