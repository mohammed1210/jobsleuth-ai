-- JobSleuth AI - Seed Data
-- This migration inserts sample job listings for development and testing

-- Insert 10 realistic job listings
INSERT INTO jobs (
    source, external_id, title, company, location, 
    salary_min, salary_max, salary_text, type, url, 
    posted_at, raw
) VALUES
(
    'manual',
    'seed-001',
    'Senior Full Stack Engineer',
    'TechCorp Inc',
    'San Francisco, CA (Remote)',
    140000,
    180000,
    '$140k - $180k',
    'Full-time',
    'https://example.com/jobs/senior-fullstack-engineer-001',
    NOW() - INTERVAL '2 days',
    '{"description": "Build scalable web applications using React and Node.js", "requirements": ["5+ years experience", "React", "Node.js", "TypeScript"], "benefits": ["Health insurance", "401k", "Remote work"]}'::jsonb
),
(
    'manual',
    'seed-002',
    'Machine Learning Engineer',
    'AI Innovations',
    'New York, NY',
    150000,
    200000,
    '$150k - $200k',
    'Full-time',
    'https://example.com/jobs/ml-engineer-002',
    NOW() - INTERVAL '1 day',
    '{"description": "Develop and deploy ML models at scale", "requirements": ["Python", "TensorFlow", "PyTorch", "3+ years ML experience"], "benefits": ["Stock options", "Health insurance", "Gym membership"]}'::jsonb
),
(
    'manual',
    'seed-003',
    'Product Designer',
    'Creative Studios',
    'Austin, TX (Hybrid)',
    90000,
    120000,
    '$90k - $120k',
    'Full-time',
    'https://example.com/jobs/product-designer-003',
    NOW() - INTERVAL '3 days',
    '{"description": "Design beautiful and intuitive user experiences", "requirements": ["Figma", "Adobe Creative Suite", "4+ years design experience"], "benefits": ["Flexible hours", "Health insurance", "Education stipend"]}'::jsonb
),
(
    'manual',
    'seed-004',
    'DevOps Engineer',
    'CloudScale Systems',
    'Seattle, WA (Remote)',
    130000,
    170000,
    '$130k - $170k',
    'Full-time',
    'https://example.com/jobs/devops-engineer-004',
    NOW() - INTERVAL '5 days',
    '{"description": "Manage cloud infrastructure and CI/CD pipelines", "requirements": ["AWS/Azure/GCP", "Kubernetes", "Docker", "Terraform"], "benefits": ["Remote work", "Unlimited PTO", "Stock options"]}'::jsonb
),
(
    'manual',
    'seed-005',
    'Frontend Developer',
    'StartupXYZ',
    'Los Angeles, CA',
    100000,
    130000,
    '$100k - $130k',
    'Full-time',
    'https://example.com/jobs/frontend-developer-005',
    NOW() - INTERVAL '1 day',
    '{"description": "Build responsive web applications with modern frameworks", "requirements": ["React or Vue", "JavaScript/TypeScript", "CSS", "3+ years experience"], "benefits": ["Stock options", "Health insurance", "Snacks and drinks"]}'::jsonb
),
(
    'manual',
    'seed-006',
    'Data Scientist',
    'Analytics Pro',
    'Boston, MA (Hybrid)',
    120000,
    160000,
    '$120k - $160k',
    'Full-time',
    'https://example.com/jobs/data-scientist-006',
    NOW() - INTERVAL '4 days',
    '{"description": "Analyze complex datasets and build predictive models", "requirements": ["Python", "R", "SQL", "Machine Learning", "Statistics"], "benefits": ["Flexible schedule", "Health insurance", "Conference budget"]}'::jsonb
),
(
    'manual',
    'seed-007',
    'Backend Engineer',
    'Enterprise Solutions Ltd',
    'Chicago, IL (Remote)',
    110000,
    145000,
    '$110k - $145k',
    'Full-time',
    'https://example.com/jobs/backend-engineer-007',
    NOW() - INTERVAL '6 days',
    '{"description": "Design and implement scalable backend services", "requirements": ["Python or Java", "Microservices", "PostgreSQL", "Redis"], "benefits": ["Remote work", "Health insurance", "401k matching"]}'::jsonb
),
(
    'manual',
    'seed-008',
    'Mobile Developer (iOS)',
    'Mobile First Inc',
    'San Diego, CA',
    115000,
    150000,
    '$115k - $150k',
    'Full-time',
    'https://example.com/jobs/ios-developer-008',
    NOW() - INTERVAL '2 days',
    '{"description": "Build native iOS applications with Swift", "requirements": ["Swift", "iOS SDK", "UIKit", "SwiftUI", "4+ years experience"], "benefits": ["Stock options", "Health insurance", "MacBook Pro"]}'::jsonb
),
(
    'manual',
    'seed-009',
    'QA Automation Engineer',
    'Quality Assurance Corp',
    'Denver, CO (Hybrid)',
    95000,
    125000,
    '$95k - $125k',
    'Full-time',
    'https://example.com/jobs/qa-automation-009',
    NOW() - INTERVAL '3 days',
    '{"description": "Develop automated testing frameworks and ensure quality", "requirements": ["Selenium", "Cypress", "Python or JavaScript", "CI/CD"], "benefits": ["Hybrid work", "Health insurance", "Training budget"]}'::jsonb
),
(
    'manual',
    'seed-010',
    'Security Engineer',
    'SecureNet Solutions',
    'Washington, DC (Remote)',
    140000,
    190000,
    '$140k - $190k',
    'Full-time',
    'https://example.com/jobs/security-engineer-010',
    NOW() - INTERVAL '7 days',
    '{"description": "Protect systems and data from security threats", "requirements": ["Security frameworks", "Penetration testing", "Network security", "5+ years experience"], "benefits": ["Remote work", "Excellent benefits", "Security clearance support"]}'::jsonb
)
ON CONFLICT (url) DO NOTHING;

-- Add a few sample companies
INSERT INTO companies (name, website) VALUES
    ('TechCorp Inc', 'https://techcorp.example.com'),
    ('AI Innovations', 'https://aiinnovations.example.com'),
    ('Creative Studios', 'https://creativestudios.example.com'),
    ('CloudScale Systems', 'https://cloudscale.example.com'),
    ('StartupXYZ', 'https://startupxyz.example.com')
ON CONFLICT DO NOTHING;
