"""
AI-powered job fit scoring service.

Computes job match scores based on resume, preferences, and job details.
Uses heuristic scoring with optional OpenAI refinement.
"""

import re
from typing import Any, Dict, List, Optional, Set
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.lib.settings import settings

# Try to import OpenAI, but don't fail if it's not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def extract_keywords(text: str) -> Set[str]:
    """
    Extract keywords from text by removing common words.
    
    Args:
        text: Input text
        
    Returns:
        Set of lowercase keywords
    """
    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract words (alphanumeric + common tech symbols)
    words = re.findall(r'\b[a-z0-9+#.]+\b', text.lower())
    return {w for w in words if w not in stop_words and len(w) > 2}


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Similarity score between 0 and 1
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def compute_title_similarity(job_title: str, resume_text: str) -> float:
    """
    Compute similarity between job title and resume using cosine similarity.
    
    Args:
        job_title: Job title
        resume_text: Resume text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not job_title or not resume_text:
        return 0.0
    
    try:
        vectorizer = CountVectorizer(stop_words='english')
        vectors = vectorizer.fit_transform([job_title.lower(), resume_text.lower()])
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        return float(similarity)
    except Exception:
        # Fallback to keyword matching
        job_keywords = extract_keywords(job_title)
        resume_keywords = extract_keywords(resume_text)
        return jaccard_similarity(job_keywords, resume_keywords)


def compute_location_score(job_location: Optional[str], preferred_locations: List[str]) -> float:
    """
    Score based on location match.
    
    Args:
        job_location: Job location string
        preferred_locations: List of preferred location patterns
        
    Returns:
        Score between 0 and 1
    """
    if not job_location:
        return 0.5  # Neutral if no location specified
    
    if not preferred_locations:
        return 0.5  # Neutral if no preferences
    
    job_loc_lower = job_location.lower()
    
    # Check for remote
    if 'remote' in job_loc_lower:
        return 1.0
    
    # Check for matches with preferred locations
    for pref_loc in preferred_locations:
        if pref_loc.lower() in job_loc_lower:
            return 1.0
    
    return 0.3  # Penalty for non-matching location


def compute_salary_score(
    job_salary_min: Optional[int],
    job_salary_max: Optional[int],
    desired_salary: Optional[int]
) -> float:
    """
    Score based on salary alignment.
    
    Args:
        job_salary_min: Job minimum salary
        job_salary_max: Job maximum salary
        desired_salary: Desired salary
        
    Returns:
        Score between 0 and 1
    """
    # Handle cases where salary is None (not 0)
    if desired_salary is None or (job_salary_min is None and job_salary_max is None):
        return 0.5  # Neutral if no salary info
    
    # Use average if both min and max available
    if job_salary_min is not None and job_salary_max is not None:
        job_salary_avg = (job_salary_min + job_salary_max) / 2
    elif job_salary_min is not None:
        job_salary_avg = job_salary_min
    elif job_salary_max is not None:
        job_salary_avg = job_salary_max
    else:
        return 0.5
    
    # IMPORTANT: Preserve zero values - don't treat 0 as falsy
    # Only return neutral score if value is None
    if job_salary_avg is None:
        return 0.5
    
    # Score based on how close to desired
    if job_salary_avg >= desired_salary:
        # Meets or exceeds desired
        return min(1.0, job_salary_avg / (desired_salary * 1.5))
    else:
        # Below desired - penalize proportionally
        return max(0.0, job_salary_avg / desired_salary)


def compute_seniority_score(job_title: str, years_experience: Optional[int]) -> float:
    """
    Score based on seniority level match.
    
    Args:
        job_title: Job title
        years_experience: Years of experience
        
    Returns:
        Score between 0 and 1
    """
    if years_experience is None:
        return 0.5
    
    title_lower = job_title.lower()
    
    # Determine job seniority level
    if any(term in title_lower for term in ['senior', 'lead', 'principal', 'staff']):
        required_years = 5
    elif any(term in title_lower for term in ['mid', 'intermediate']):
        required_years = 3
    elif any(term in title_lower for term in ['junior', 'entry']):
        required_years = 1
    else:
        # Default to mid-level
        required_years = 3
    
    # Score based on experience alignment
    if years_experience >= required_years:
        return 1.0
    else:
        return max(0.3, years_experience / required_years)


async def compute_heuristic_score(
    job: Dict[str, Any],
    resume_text: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute job fit score using heuristic methods.
    
    Args:
        job: Job dictionary with fields like title, location, salary_min, etc.
        resume_text: Optional resume text for skills matching
        preferences: Optional user preferences
        
    Returns:
        Dictionary with fit_score (0-100) and factors
    """
    factors = []
    weights = []
    
    # Extract job details
    job_title = job.get('title', '')
    job_location = job.get('location')
    job_salary_min = job.get('salary_min')
    job_salary_max = job.get('salary_max')
    job_description = job.get('raw', {}).get('description', '') if job.get('raw') else ''
    
    # Extract preferences
    preferred_locations = preferences.get('locations', []) if preferences else []
    desired_salary = preferences.get('salary') if preferences else None
    years_experience = preferences.get('years_experience') if preferences else None
    
    # 1. Skills match (highest weight)
    if resume_text and (job_title or job_description):
        job_text = f"{job_title} {job_description}"
        title_score = compute_title_similarity(job_text, resume_text)
        
        factors.append({
            'name': 'Skills Match',
            'score': round(title_score * 100, 1),
            'weight': 0.35
        })
        weights.append(title_score * 0.35)
    
    # 2. Location match
    location_score = compute_location_score(job_location, preferred_locations)
    factors.append({
        'name': 'Location',
        'score': round(location_score * 100, 1),
        'weight': 0.25
    })
    weights.append(location_score * 0.25)
    
    # 3. Salary match
    salary_score = compute_salary_score(job_salary_min, job_salary_max, desired_salary)
    factors.append({
        'name': 'Salary Fit',
        'score': round(salary_score * 100, 1),
        'weight': 0.25
    })
    weights.append(salary_score * 0.25)
    
    # 4. Seniority match
    seniority_score = compute_seniority_score(job_title, years_experience)
    factors.append({
        'name': 'Seniority Level',
        'score': round(seniority_score * 100, 1),
        'weight': 0.15
    })
    weights.append(seniority_score * 0.15)
    
    # Calculate weighted average
    total_score = sum(weights) / sum(f['weight'] for f in factors) if factors else 0
    fit_score = round(total_score * 100, 1)
    
    return {
        'fit_score': fit_score,
        'factors': factors,
        'method': 'heuristic'
    }


async def refine_with_openai(
    job: Dict[str, Any],
    resume_text: str,
    heuristic_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Refine heuristic score using OpenAI.
    
    Args:
        job: Job dictionary
        resume_text: Resume text
        heuristic_result: Heuristic scoring result
        
    Returns:
        Refined scoring result
    """
    if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
        return heuristic_result
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""Given this job and resume, refine the job fit score (currently {heuristic_result['fit_score']}/100).

Job Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('raw', {}).get('description', '')[:500]}

Resume: {resume_text[:1000]}

Heuristic Factors:
{heuristic_result['factors']}

Provide a refined score (0-100) and brief justification. Be realistic and honest."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a job matching expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        ai_response = response.choices[0].message.content
        
        # Try to extract score from response
        score_match = re.search(r'\b(\d{1,3})\b', ai_response)
        if score_match:
            refined_score = min(100, max(0, int(score_match.group(1))))
            return {
                'fit_score': refined_score,
                'factors': heuristic_result['factors'],
                'method': 'ai_refined',
                'ai_insight': ai_response
            }
    except Exception as e:
        # If OpenAI fails, return heuristic result
        print(f"OpenAI refinement failed: {e}")
    
    return heuristic_result


async def score_job(
    job: Dict[str, Any],
    resume_text: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
    use_ai: bool = True
) -> Dict[str, Any]:
    """
    Score a job for a user.
    
    Args:
        job: Job dictionary
        resume_text: Optional resume text
        preferences: Optional user preferences
        use_ai: Whether to use AI refinement if available
        
    Returns:
        Scoring result with fit_score and factors
    """
    # Compute heuristic score
    result = await compute_heuristic_score(job, resume_text, preferences)
    
    # Refine with AI if requested and available
    if use_ai and resume_text and settings.OPENAI_API_KEY:
        result = await refine_with_openai(job, resume_text, result)
    
    return result
