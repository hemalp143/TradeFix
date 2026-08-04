import logging
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import numpy as np
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)


class JobWorkerMatcher:
    """Intelligent job-to-worker matching engine using semantic similarity and multi-factor scoring."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize matcher with embedding model."""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def match_worker_to_job(
        self,
        job,
        worker,
        min_score: float = 0.65
    ) -> Dict:
        """
        Calculate match score between a worker and a job.

        Returns:
            {
                'worker_id': 1,
                'job_id': 5,
                'skills_match': 0.95,
                'experience_match': 1.0,
                'availability_match': 0.8,
                'location_match': 0.9,
                'rating_match': 0.96,
                'overall_score': 0.938,
                'reasoning': "High match: skills & experience aligned, 2 miles away"
            }
        """

        # Calculate individual match components
        skills_match = self._calculate_skills_match(job.required_skills, worker.skills)
        experience_match = self._calculate_experience_match(
            job.experience_required, worker.experience_years
        )
        availability_match = self._calculate_availability_match(
            job.scheduled_date, job.scheduled_time, worker.availability
        )
        location_match = self._calculate_location_match(
            job.latitude, job.longitude, worker.latitude, worker.longitude, job.radius
        )
        rating_match = self._calculate_rating_match(worker.rating, worker.rating_count)

        # Weighted overall score
        overall_score = (
            0.30 * skills_match +
            0.25 * experience_match +
            0.20 * availability_match +
            0.15 * location_match +
            0.10 * rating_match
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            job, worker, skills_match, location_match, rating_match
        )

        return {
            'worker_id': worker.id,
            'job_id': job.id,
            'skills_match': round(skills_match, 3),
            'experience_match': round(experience_match, 3),
            'availability_match': round(availability_match, 3),
            'location_match': round(location_match, 3),
            'rating_match': round(rating_match, 3),
            'overall_score': round(overall_score, 3),
            'reasoning': reasoning,
            'meets_minimum': overall_score >= min_score
        }

    def find_best_workers_for_job(
        self,
        job,
        candidate_workers: List,
        top_n: int = 5,
        min_score: float = 0.65
    ) -> List[Dict]:
        """Find top N workers for a given job."""

        matches = []
        for worker in candidate_workers:
            match = self.match_worker_to_job(job, worker, min_score)
            if match['overall_score'] >= min_score:
                matches.append(match)

        # Sort by score descending
        matches.sort(key=lambda x: x['overall_score'], reverse=True)

        return matches[:top_n]

    def find_best_jobs_for_worker(
        self,
        worker,
        available_jobs: List,
        top_n: int = 5,
        min_score: float = 0.65
    ) -> List[Dict]:
        """Find top N jobs for a given worker."""

        matches = []
        for job in available_jobs:
            match = self.match_worker_to_job(job, worker, min_score)
            if match['overall_score'] >= min_score:
                matches.append(match)

        # Sort by score descending
        matches.sort(key=lambda x: x['overall_score'], reverse=True)

        return matches[:top_n]

    def _calculate_skills_match(self, required_skills: List[str], worker_skills: List[str]) -> float:
        """
        Calculate skills match using semantic similarity.

        Score 0-1:
        - 1.0: All required skills present
        - 0.8-0.9: Most skills present
        - 0.5-0.8: Some skills match
        - <0.5: Minimal skill overlap
        """

        if not required_skills or not worker_skills:
            return 0.0 if required_skills else 1.0

        if self.model is None:
            # Fallback: simple set intersection
            intersection = set(required_skills) & set(worker_skills)
            return len(intersection) / len(required_skills) if required_skills else 0.0

        try:
            # Encode skills
            required_embeddings = self.model.encode(required_skills, convert_to_tensor=True)
            worker_embeddings = self.model.encode(worker_skills, convert_to_tensor=True)

            # Calculate cosine similarity
            scores = []
            for req_skill in required_embeddings:
                max_similarity = max([
                    util.pytorch_cos_sim(req_skill, worker_skill)[0][0].item()
                    for worker_skill in worker_embeddings
                ])
                scores.append(max_similarity)

            # Average match score for all required skills
            avg_match = np.mean(scores)
            return float(np.clip(avg_match, 0.0, 1.0))

        except Exception as e:
            logger.error(f"Error calculating skills match: {e}")
            return 0.5  # Default to medium match on error

    def _calculate_experience_match(self, required_years: int, worker_years: int) -> float:
        """
        Experience match score.

        - 1.0: Worker has >= required experience
        - 0.8: Worker has 90%+ of required
        - 0.5: Worker has 50%+ of required
        - 0.0: Worker has less than 50% required
        """

        if required_years == 0:
            return 1.0

        if worker_years >= required_years:
            return 1.0

        ratio = worker_years / required_years
        return float(np.clip(ratio, 0.0, 1.0))

    def _calculate_availability_match(self, job_date: datetime, job_time: str, availability: Dict) -> float:
        """
        Check if worker is available for job.

        availability format: {"mon": [9, 17], "tue": [9, 17]}
        job_time format: "09:00-17:00"

        Returns 1.0 if available, 0.0 if not, 0.5 if partial.
        """

        try:
            if not availability:
                return 0.5  # Unknown availability

            day_name = job_date.strftime('%a').lower()
            if day_name not in availability:
                return 0.0  # Not available that day

            available_hours = availability[day_name]
            if not available_hours or len(available_hours) < 2:
                return 0.5

            job_start, job_end = map(int, job_time.split('-'))
            available_start, available_end = available_hours[0], available_hours[1]

            # Check if job fits in available hours
            if job_start >= available_start and job_end <= available_end:
                return 1.0
            elif job_start < available_end and job_end > available_start:
                return 0.5  # Partial overlap
            else:
                return 0.0  # No overlap

        except Exception as e:
            logger.error(f"Error calculating availability: {e}")
            return 0.5

    def _calculate_location_match(
        self, job_lat: float, job_lon: float, worker_lat: float, worker_lon: float, radius: float
    ) -> float:
        """
        Location match based on distance.

        Returns 1.0 if within radius, scales down linearly beyond radius.
        """

        try:
            distance = self._haversine_distance(job_lat, job_lon, worker_lat, worker_lon)

            if distance <= radius:
                # Within radius: score 1.0 at 0 miles, 0.7 at max radius
                return 0.7 + (0.3 * (1 - distance / radius))

            # Beyond radius: scale down
            return max(0.2, 0.7 - (distance - radius) / radius * 0.5)

        except Exception as e:
            logger.error(f"Error calculating location match: {e}")
            return 0.5

    def _calculate_rating_match(self, rating: float, rating_count: int) -> float:
        """
        Rating match score.

        Considers both rating and confidence (number of ratings).
        - 5.0+ rating with 10+ ratings = 1.0
        - 4.0+ rating with 5+ ratings = 0.8
        - 3.0+ rating = 0.6
        - <3.0 rating = 0.3
        """

        if rating_count == 0:
            return 0.5  # Unknown

        if rating >= 4.8:
            return 1.0
        elif rating >= 4.0:
            return 0.9
        elif rating >= 3.5:
            return 0.8
        elif rating >= 3.0:
            return 0.6
        elif rating >= 2.5:
            return 0.4
        else:
            return 0.2

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points on Earth (in miles).

        lat/lon in decimal degrees.
        """

        try:
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))

            miles = 3959 * c  # Earth radius in miles
            return miles

        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return 999.0

    def _generate_reasoning(
        self, job, worker, skills_match: float, location_match: float, rating_match: float
    ) -> str:
        """Generate human-readable explanation of match score."""

        reasons = []

        # Skills
        if skills_match >= 0.9:
            reasons.append("High skill match")
        elif skills_match >= 0.7:
            reasons.append("Good skill overlap")
        else:
            reasons.append("Moderate skill fit")

        # Location
        try:
            distance = self._haversine_distance(
                job.latitude, job.longitude, worker.latitude, worker.longitude
            )
            reasons.append(f"{distance:.1f} miles away")
        except:
            pass

        # Rating
        if worker.rating >= 4.5:
            reasons.append("High-rated worker")
        elif worker.rating >= 4.0:
            reasons.append("Reliable track record")

        return ", ".join(reasons)
