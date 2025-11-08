"""AI-powered job scoring service for JobSleuth AI."""

import re
from typing import Any, Dict, List, Optional

from lib.settings import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def extract_skills(text: str) -> set[str]:
    """Extract skills from text (simple tokenization)."""
    if not text:
        return set()
    
    # Common programming languages and technologies
    tech_keywords = {
        "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "go", "rust",
        "react", "angular", "vue", "node", "django", "flask", "fastapi", "express",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mongodb", "redis", "graphql",
        "machine learning", "ml", "ai", "data science", "analytics"
    }
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in tech_keywords:
        if skill in text_lower:
            found_skills.add(skill)
    
    return found_skills


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 0.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def title_similarity(job_title: str, resume_text: str) -> float:
    """Calculate title similarity using token overlap."""
    if not job_title or not resume_text:
        return 0.0
    
    # Extract key words from title (remove common words)
    stop_words = {"the", "a", "an", "and", "or", "for", "to", "in", "at", "of"}
    title_tokens = {
        word.lower() 
        for word in re.findall(r'\w+', job_title) 
        if word.lower() not in stop_words and len(word) > 2
    }
    
    resume_lower = resume_text.lower()
    matches = sum(1 for token in title_tokens if token in resume_lower)
    
    return matches / len(title_tokens) if title_tokens else 0.0


def salary_fit(job_salary_min: Optional[int], job_salary_max: Optional[int]) -> float:
    """Score salary fit (higher is better)."""
    # If no salary info, neutral score
    if job_salary_min is None and job_salary_max is None:
        return 0.5
    
    # If we have salary info, give it a reasonable score based on range
    salary_avg = 0
    if job_salary_min is not None and job_salary_max is not None:
        salary_avg = (job_salary_min + job_salary_max) / 2
    elif job_salary_min is not None:
        salary_avg = job_salary_min
    elif job_salary_max is not None:
        salary_avg = job_salary_max
    
    # Normalize salary (100k-200k range is typical)
    if salary_avg == 0:
        return 0.5
    
    # Score higher salaries better (capped at 1.0)
    normalized = min((salary_avg - 50000) / 150000, 1.0)
    return max(0.0, normalized)


def compute_heuristic_score(job: Dict[str, Any], resume_text: Optional[str]) -> Dict[str, Any]:
    """Compute heuristic-based job fit score.
    
    IMPORTANT: Never treat 0 as falsy. Only use None checks for missing values.
    """
    factors = []
    
    # Extract job details
    job_title = job.get("title", "")
    job_desc = job.get("raw", {}).get("description", "") if isinstance(job.get("raw"), dict) else ""
    job_skills_text = job_desc + " " + job_title
    
    # Skills overlap
    job_skills = extract_skills(job_skills_text)
    resume_skills = extract_skills(resume_text) if resume_text else set()
    
    skills_score = jaccard_similarity(job_skills, resume_skills) if resume_text else 0.0
    # IMPORTANT: Check for None, not falsiness. 0.0 is a valid score.
    if skills_score is not None:
        factors.append({
            "name": "Skills Match",
            "score": skills_score,
            "weight": 0.4,
        })
    
    # Title similarity
    title_score = title_similarity(job_title, resume_text) if resume_text else 0.0
    if title_score is not None:
        factors.append({
            "name": "Title Relevance",
            "score": title_score,
            "weight": 0.3,
        })
    
    # Salary fit (IMPORTANT: preserve 0 values)
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    sal_score = salary_fit(salary_min, salary_max)
    if sal_score is not None:
        factors.append({
            "name": "Salary Range",
            "score": sal_score,
            "weight": 0.2,
        })
    
    # Location preference (simplified - always give neutral score if present)
    location = job.get("location")
    if location:
        factors.append({
            "name": "Location",
            "score": 0.5,
            "weight": 0.1,
        })
    
    # Calculate weighted average (IMPORTANT: 0 is valid)
    total_weight = sum(f["weight"] for f in factors)
    weighted_sum = sum(f["score"] * f["weight"] for f in factors)
    
    fit_score = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0
    
    return {
        "fit_score": round(fit_score, 2),
        "factors": factors,
        "method": "heuristic",
    }


async def compute_ai_score(job: Dict[str, Any], resume_text: Optional[str]) -> Dict[str, Any]:
    """Compute AI-enhanced job fit score using OpenAI."""
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        return compute_heuristic_score(job, resume_text)
    
    # Get heuristic baseline
    heuristic_result = compute_heuristic_score(job, resume_text)
    
    # If no resume provided, return heuristic only
    if not resume_text:
        return heuristic_result
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""Analyze this job fit:

Job: {job.get('title', '')} at {job.get('company', '')}
Description: {job.get('raw', {}).get('description', '')[:500] if isinstance(job.get('raw'), dict) else ''}

Resume snippet: {resume_text[:1000]}

Provide a fit score 0-100 and key factors. Response format:
Score: [number]
Factors: [brief list]
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        
        ai_text = response.choices[0].message.content or ""
        
        # Parse AI response
        score_match = re.search(r'Score:\s*(\d+)', ai_text)
        ai_score = float(score_match.group(1)) if score_match else heuristic_result["fit_score"]
        
        # Blend AI and heuristic scores
        final_score = (ai_score * 0.6 + heuristic_result["fit_score"] * 0.4)
        
        return {
            "fit_score": round(final_score, 2),
            "factors": heuristic_result["factors"],
            "method": "ai_enhanced",
            "ai_reasoning": ai_text[:500],
        }
    except Exception:
        # Fallback to heuristic on any error
        return heuristic_result
