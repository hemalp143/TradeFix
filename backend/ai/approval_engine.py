import logging
from typing import Dict, Tuple
from app.models import Worker, ApprovalDecision
from app.config import settings
import re

logger = logging.getLogger(__name__)


class AutoApprovalEngine:
    """Automated approval/rejection decision engine for worker registration."""

    def __init__(self):
        self.auto_approve_threshold = settings.approval_auto_threshold  # >= 80
        self.auto_reject_threshold = settings.approval_review_threshold  # < 50

    def evaluate_worker(self, worker: Worker) -> Tuple[float, ApprovalDecision, str, Dict]:
        """
        Evaluate a worker for automatic approval.

        Args:
            worker: Worker model instance

        Returns:
            (score, decision, reasoning, factors)
            where score is 0-100, decision is auto_approve/auto_reject/manual_review
        """

        factors = {}
        score = 0.0

        # 1. Email Validation (10 points)
        email_score = self._validate_email(worker.email)
        factors['email_valid'] = email_score == 10
        score += email_score

        # 2. Experience Level (20 points)
        exp_score = self._score_experience(worker.experience_years)
        factors['experience_years'] = worker.experience_years
        factors['experience_score'] = exp_score
        score += exp_score

        # 3. Skills Validation (15 points)
        skills_score = self._score_skills(worker.skills)
        factors['skills_count'] = len(worker.skills)
        factors['skills_score'] = skills_score
        score += skills_score

        # 4. Postal Code Validity (10 points)
        postal_score = self._validate_postal_code(worker.postal_code)
        factors['postal_code_valid'] = postal_score == 10
        score += postal_score

        # 5. Subscription Tier (15 points)
        tier_score = self._score_subscription_tier(str(worker.subscription_tier))
        factors['subscription_tier'] = str(worker.subscription_tier)
        factors['tier_score'] = tier_score
        score += tier_score

        # 6. Phone Validation (10 points)
        phone_score = self._validate_phone(worker.phone)
        factors['phone_valid'] = phone_score == 10
        score += phone_score

        # 7. Bio/Profile Completeness (10 points)
        bio_score = self._score_profile_completeness(worker.bio)
        factors['has_bio'] = bool(worker.bio)
        factors['bio_score'] = bio_score
        score += bio_score

        # Clamp score to 0-100
        score = min(100, max(0, score))

        # Make decision
        if score >= self.auto_approve_threshold:
            decision = ApprovalDecision.AUTO_APPROVE
            reasoning = f"Auto-approved: Score {score:.1f} meets approval threshold ({self.auto_approve_threshold})"
        elif score < self.auto_reject_threshold:
            decision = ApprovalDecision.AUTO_REJECT
            reasoning = f"Auto-rejected: Score {score:.1f} below review threshold ({self.auto_reject_threshold})"
        else:
            decision = ApprovalDecision.MANUAL_REVIEW
            reasoning = f"Manual review required: Score {score:.1f} between thresholds"

        logger.info(f"Worker {worker.id} evaluation: score={score}, decision={decision.value}")

        return score, decision, reasoning, factors

    def _validate_email(self, email: str) -> float:
        """Validate email format. Returns 0 or 10."""
        if not email:
            return 0.0

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_regex, email):
            return 10.0
        return 0.0

    def _score_experience(self, years: int) -> float:
        """Score experience level. 0-20 points."""
        if years >= 5:
            return 20.0  # Senior: full points
        elif years >= 3:
            return 15.0  # Intermediate
        elif years >= 1:
            return 10.0  # Beginner
        elif years > 0:
            return 5.0  # Learning
        else:
            return 0.0  # No experience

    def _score_skills(self, skills: list) -> float:
        """Score skills diversity. 0-15 points."""
        if not skills:
            return 0.0

        num_skills = len(skills)
        if num_skills >= 5:
            return 15.0  # Full points for 5+ skills
        elif num_skills >= 3:
            return 12.0
        elif num_skills >= 2:
            return 8.0
        else:
            return 4.0

    def _validate_postal_code(self, postal_code: str) -> float:
        """Validate postal code format (UK). Returns 0 or 10."""
        if not postal_code:
            return 0.0

        # UK postal code format: A9A 9AA
        uk_postcode_regex = r'^[A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2}$'
        if re.match(uk_postcode_regex, postal_code.strip().upper()):
            return 10.0
        return 0.0

    def _score_subscription_tier(self, tier: str) -> float:
        """Prioritize paid tiers. 0-15 points."""
        tier_scores = {
            'enterprise': 15.0,
            'professional': 12.0,
            'starter': 5.0
        }
        return tier_scores.get(tier.lower(), 0.0)

    def _validate_phone(self, phone: str) -> float:
        """Validate phone format. Returns 0 or 10."""
        if not phone:
            return 5.0  # Optional but encouraged

        # Simple validation: 10-15 digits
        digits = ''.join(filter(str.isdigit, phone))
        if 10 <= len(digits) <= 15:
            return 10.0
        return 0.0

    def _score_profile_completeness(self, bio: str) -> float:
        """Score profile completeness. 0-10 points."""
        if not bio:
            return 0.0

        bio_length = len(bio.strip())
        if bio_length >= 100:
            return 10.0
        elif bio_length >= 50:
            return 7.0
        elif bio_length > 0:
            return 3.0
        return 0.0

    def batch_evaluate_workers(self, workers: list) -> list:
        """Evaluate multiple workers and return results."""
        results = []
        for worker in workers:
            score, decision, reasoning, factors = self.evaluate_worker(worker)
            results.append({
                'worker_id': worker.id,
                'email': worker.email,
                'score': score,
                'decision': decision.value,
                'reasoning': reasoning,
                'factors': factors
            })
        return results

    def auto_approve_eligible_workers(self, workers: list) -> Tuple[list, list]:
        """
        Separate workers into auto-approve and manual-review groups.

        Returns:
            (auto_approve_list, manual_review_list)
        """
        auto_approve = []
        manual_review = []

        for worker in workers:
            score, decision, reasoning, factors = self.evaluate_worker(worker)

            if decision == ApprovalDecision.AUTO_APPROVE:
                auto_approve.append({
                    'worker': worker,
                    'score': score,
                    'reasoning': reasoning
                })
            else:
                manual_review.append({
                    'worker': worker,
                    'score': score,
                    'decision': decision,
                    'reasoning': reasoning,
                    'factors': factors
                })

        return auto_approve, manual_review


class ApprovalRulesEngine:
    """Rules-based approval engine for additional logic."""

    @staticmethod
    def check_duplicate_email(email: str, db) -> bool:
        """Check if email already registered."""
        from app.models import Worker
        existing = db.query(Worker).filter(Worker.email == email).first()
        return existing is not None

    @staticmethod
    def check_suspicious_activity(worker: Worker, db) -> bool:
        """Check for suspicious registration patterns."""
        from app.models import WorkerActivityLog
        from datetime import timedelta, datetime

        # Check for multiple registrations from same postal code in short time
        recent_registrations = db.query(WorkerActivityLog).filter(
            WorkerActivityLog.action == "registered",
            WorkerActivityLog.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()

        # Flag if >3 registrations in 1 hour
        return recent_registrations > 3

    @staticmethod
    def check_geographic_coverage(postal_code: str, db) -> bool:
        """Check if postal code is in service area."""
        from app.models import PostalCodeArea
        # This assumes you have a PostalCodeArea table
        # For now, return True (all postal codes valid)
        return True
