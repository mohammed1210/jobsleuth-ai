"""AI-powered job scoring system for JobSleuth.

Computes heuristic scores based on:
- Skills overlap (Jaccard similarity)
- Title similarity (token cosine similarity)
- Location tolerance
- Salary fit
- Seniority match

Never treats 0 as falsy; only defaults when value is None.
Optionally refines scores using OpenAI if API key is present.
"""

import os
import re
from typing import Any, Optional
from collections import Counter
import math


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Jaccard similarity coefficient (0.0 to 1.0)
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Calculate cosine similarity between two token frequency vectors.
    
    Args:
        vec1: First vector (token -> frequency)
        vec2: Second vector (token -> frequency)
        
    Returns:
        Cosine similarity (0.0 to 1.0)
    """
    if not vec1 or not vec2:
        return 0.0
    
    # Calculate dot product
    dot_product = sum(vec1.get(token, 0) * vec2.get(token, 0) for token in set(vec1) | set(vec2))
    
    # Calculate magnitudes
    mag1 = math.sqrt(sum(count ** 2 for count in vec1.values()))
    mag2 = math.sqrt(sum(count ** 2 for count in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words.
    
    Args:
        text: Text to tokenize
        
    Returns:
        List of tokens
    """
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return [token for token in text.split() if len(token) > 2]


def calculate_skills_overlap(user_skills: list[str], job_skills: list[str]) -> float:
    """Calculate skills overlap using Jaccard similarity.
    
    Args:
        user_skills: List of user's skills
        job_skills: List of job's required skills
        
    Returns:
        Skills overlap score (0.0 to 1.0)
    """
    if job_skills is None or len(job_skills) == 0:
        # If no job skills are specified, return neutral score
        return 0.5
    
    if user_skills is None or len(user_skills) == 0:
        # If user has no skills, return 0 (not falsy check!)
        return 0.0
    
    # Normalize skills to lowercase sets
    user_set = set(skill.lower().strip() for skill in user_skills)
    job_set = set(skill.lower().strip() for skill in job_skills)
    
    return jaccard_similarity(user_set, job_set)


def calculate_title_similarity(user_title: str, job_title: str) -> float:
    """Calculate title similarity using token cosine similarity.
    
    Args:
        user_title: User's current/desired job title
        job_title: Job posting title
        
    Returns:
        Title similarity score (0.0 to 1.0)
    """
    if not job_title:
        return 0.0
    
    if not user_title:
        return 0.5  # Neutral score if user has no title preference
    
    # Tokenize and create frequency vectors
    user_tokens = tokenize(user_title)
    job_tokens = tokenize(job_title)
    
    user_vec = Counter(user_tokens)
    job_vec = Counter(job_tokens)
    
    return cosine_similarity(user_vec, job_vec)


def calculate_location_fit(user_location: str, job_location: str, remote_ok: bool = False) -> float:
    """Calculate location fit score.
    
    Args:
        user_location: User's preferred location
        job_location: Job location
        remote_ok: Whether user accepts remote positions
        
    Returns:
        Location fit score (0.0 to 1.0)
    """
    if not job_location:
        return 0.5  # Neutral if job location not specified
    
    job_location_lower = job_location.lower()
    
    # Check if job is remote
    if "remote" in job_location_lower:
        return 1.0 if remote_ok else 0.3
    
    if not user_location:
        return 0.5  # Neutral if no user preference
    
    user_location_lower = user_location.lower()
    
    # Simple matching: check if locations share common tokens
    user_tokens = set(tokenize(user_location_lower))
    job_tokens = set(tokenize(job_location_lower))
    
    if user_tokens.intersection(job_tokens):
        return 1.0
    
    return 0.0


def calculate_salary_fit(
    user_min_salary: Optional[float],
    user_max_salary: Optional[float],
    job_salary_min: Optional[float],
    job_salary_max: Optional[float]
) -> float:
    """Calculate salary fit score.
    
    Args:
        user_min_salary: User's minimum acceptable salary
        user_max_salary: User's maximum expected salary
        job_salary_min: Job's minimum salary
        job_salary_max: Job's maximum salary
        
    Returns:
        Salary fit score (0.0 to 1.0)
    """
    # Note: Explicitly check for None, not falsy (0 is valid!)
    if job_salary_min is None and job_salary_max is None:
        return 0.5  # Neutral if job salary not specified
    
    if user_min_salary is None:
        return 0.5  # Neutral if no user preference
    
    # Get effective salary ranges
    job_min = job_salary_min if job_salary_min is not None else 0
    job_max = job_salary_max if job_salary_max is not None else float('inf')
    user_max = user_max_salary if user_max_salary is not None else float('inf')
    
    # Check if ranges overlap
    if job_max >= user_min_salary and job_min <= user_max:
        # Calculate overlap ratio
        overlap_start = max(job_min, user_min_salary)
        overlap_end = min(job_max, user_max)
        overlap = overlap_end - overlap_start
        
        user_range = user_max - user_min_salary if user_max != float('inf') else job_max - user_min_salary
        
        if user_range > 0:
            return min(1.0, overlap / user_range)
        else:
            return 1.0
    
    # If job salary is below user minimum
    if job_max < user_min_salary:
        # Penalize based on how far below
        gap = user_min_salary - job_max
        penalty = min(1.0, gap / user_min_salary)
        return max(0.0, 1.0 - penalty)
    
    # If job salary is above user maximum
    if job_min > user_max:
        # This is actually good! Return high score
        return 0.8
    
    return 0.0


def calculate_seniority_match(user_level: str, job_level: str) -> float:
    """Calculate seniority level match.
    
    Args:
        user_level: User's seniority level
        job_level: Job's required seniority level
        
    Returns:
        Seniority match score (0.0 to 1.0)
    """
    if not job_level:
        return 0.5  # Neutral if not specified
    
    if not user_level:
        return 0.5  # Neutral if no preference
    
    # Define seniority hierarchy
    levels = {
        "intern": 1,
        "entry": 2,
        "junior": 3,
        "mid": 4,
        "senior": 5,
        "lead": 6,
        "principal": 7,
        "staff": 7,
        "director": 8,
        "vp": 9,
        "executive": 10,
    }
    
    # Normalize and find level
    user_level_lower = user_level.lower()
    job_level_lower = job_level.lower()
    
    user_num = None
    job_num = None
    
    for key, value in levels.items():
        if key in user_level_lower:
            user_num = value
        if key in job_level_lower:
            job_num = value
    
    if user_num is None or job_num is None:
        return 0.5  # Can't determine, neutral score
    
    # Perfect match
    if user_num == job_num:
        return 1.0
    
    # Calculate penalty based on distance
    distance = abs(user_num - job_num)
    max_distance = max(levels.values()) - min(levels.values())
    
    return max(0.0, 1.0 - (distance / max_distance))


def calculate_heuristic_score(
    user_profile: dict[str, Any],
    job: dict[str, Any]
) -> dict[str, Any]:
    """Calculate heuristic job fit score.
    
    Args:
        user_profile: User profile with preferences
        job: Job posting data
        
    Returns:
        Dictionary with overall score and component scores
    """
    # Calculate component scores
    skills_score = calculate_skills_overlap(
        user_profile.get("skills", []),
        job.get("required_skills", [])
    )
    
    title_score = calculate_title_similarity(
        user_profile.get("desired_title", ""),
        job.get("title", "")
    )
    
    location_score = calculate_location_fit(
        user_profile.get("location", ""),
        job.get("location", ""),
        user_profile.get("remote_ok", False)
    )
    
    salary_score = calculate_salary_fit(
        user_profile.get("min_salary"),
        user_profile.get("max_salary"),
        job.get("salary_min"),
        job.get("salary_max")
    )
    
    seniority_score = calculate_seniority_match(
        user_profile.get("seniority_level", ""),
        job.get("seniority_level", "")
    )
    
    # Weighted average (you can adjust weights)
    weights = {
        "skills": 0.35,
        "title": 0.25,
        "location": 0.15,
        "salary": 0.15,
        "seniority": 0.10,
    }
    
    overall_score = (
        weights["skills"] * skills_score +
        weights["title"] * title_score +
        weights["location"] * location_score +
        weights["salary"] * salary_score +
        weights["seniority"] * seniority_score
    )
    
    return {
        "overall_score": round(overall_score, 3),
        "skills_score": round(skills_score, 3),
        "title_score": round(title_score, 3),
        "location_score": round(location_score, 3),
        "salary_score": round(salary_score, 3),
        "seniority_score": round(seniority_score, 3),
    }


async def refine_with_llm(
    user_profile: dict[str, Any],
    job: dict[str, Any],
    heuristic_scores: dict[str, Any]
) -> dict[str, Any]:
    """Refine heuristic scores using OpenAI LLM.
    
    Args:
        user_profile: User profile
        job: Job posting
        heuristic_scores: Heuristic scores to refine
        
    Returns:
        Refined scores
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Return heuristic scores unchanged
        return heuristic_scores
    
    try:
        import openai
        
        openai.api_key = api_key
        
        # Construct prompt
        prompt = f"""You are a job matching expert. Review the following job fit analysis and provide a refined overall score (0.0 to 1.0).

User Profile:
- Skills: {', '.join(user_profile.get('skills', []))}
- Desired Title: {user_profile.get('desired_title', 'N/A')}
- Location: {user_profile.get('location', 'N/A')} (Remote OK: {user_profile.get('remote_ok', False)})
- Salary Range: ${user_profile.get('min_salary', 'N/A')} - ${user_profile.get('max_salary', 'N/A')}
- Seniority: {user_profile.get('seniority_level', 'N/A')}

Job:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'N/A')}
- Salary: ${job.get('salary_min', 'N/A')} - ${job.get('salary_max', 'N/A')}
- Required Skills: {', '.join(job.get('required_skills', []))}

Heuristic Scores:
- Overall: {heuristic_scores['overall_score']}
- Skills: {heuristic_scores['skills_score']}
- Title: {heuristic_scores['title_score']}
- Location: {heuristic_scores['location_score']}
- Salary: {heuristic_scores['salary_score']}
- Seniority: {heuristic_scores['seniority_score']}

Provide only a refined overall score as a decimal (e.g., 0.85)."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a job matching expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        refined_score_str = response.choices[0].message.content.strip()
        refined_score = float(refined_score_str)
        
        # Validate score is in range
        refined_score = max(0.0, min(1.0, refined_score))
        
        return {
            **heuristic_scores,
            "overall_score": round(refined_score, 3),
            "llm_refined": True,
        }
    except Exception as e:
        print(f"Failed to refine with LLM: {e}")
        return heuristic_scores


async def score_job(
    user_profile: dict[str, Any],
    job: dict[str, Any],
    use_llm: bool = True
) -> dict[str, Any]:
    """Score a job for a user.
    
    Args:
        user_profile: User profile with preferences
        job: Job posting data
        use_llm: Whether to use LLM refinement (if available)
        
    Returns:
        Job scores
    """
    heuristic_scores = calculate_heuristic_score(user_profile, job)
    
    if use_llm and os.getenv("OPENAI_API_KEY"):
        return await refine_with_llm(user_profile, job, heuristic_scores)
    
    return heuristic_scores
