from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Enum, LargeBinary, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SubscriptionTier(str, enum.Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class JobStatus(str, enum.Enum):
    OPEN = "open"
    MATCHED = "matched"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MatchStatus(str, enum.Enum):
    SUGGESTED = "suggested"
    APPLIED = "applied"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ApprovalDecision(str, enum.Enum):
    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    MANUAL_REVIEW = "manual_review"


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String, nullable=True)
    password_hash = Column(String)

    # Location
    postal_code = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    # Profile
    skills = Column(JSON, default=list)  # ["plumbing", "gas_fitting"]
    experience_years = Column(Integer, default=0)
    hourly_rate = Column(Float, default=0.0)
    availability = Column(JSON, default=dict)  # {"mon": [9, 17], "tue": [9, 17]}
    bio = Column(Text, nullable=True)

    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.STARTER)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)

    # Status & Scoring
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
    approval_score = Column(Float, default=0.0)  # 0-100
    matched_jobs = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Embeddings
    embedding = Column(LargeBinary, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_postal_code_approval', 'postal_code', 'approval_status'),
        Index('idx_skills_rating', 'rating'),
    )


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String, index=True)  # "plumbing", "electrical"

    # Requirements
    required_skills = Column(JSON, default=list)  # ["plumbing", "emergency"]
    experience_required = Column(Integer, default=0)
    pay_rate = Column(Float)
    duration_hours = Column(Float)

    # Location
    postal_code = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float, default=25.0)  # miles

    # Timeline
    scheduled_date = Column(DateTime, index=True)
    scheduled_time = Column(String)  # "09:00-17:00"
    deadline = Column(DateTime)

    # Status
    status = Column(Enum(JobStatus), default=JobStatus.OPEN, index=True)
    priority = Column(Enum(JobPriority), default=JobPriority.MEDIUM)

    # Client
    client_id = Column(Integer, ForeignKey("clients.id"))
    client_name = Column(String)
    client_rating = Column(Float, default=0.0)

    # Matching
    matched_workers = Column(JSON, default=list)  # [{"worker_id": 1, "score": 0.92}, ...]
    assigned_worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)

    # AI Predictions
    estimated_completion_time = Column(Float, nullable=True)
    demand_score = Column(Float, default=50.0)  # 0-100

    # Metadata
    embedding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_postal_status_date', 'postal_code', 'status', 'scheduled_date'),
        Index('idx_status_priority', 'status', 'priority'),
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), index=True)

    # Match Scores
    skills_match = Column(Float)  # 0-1
    experience_match = Column(Float)  # 0-1
    availability_match = Column(Float)  # 0-1
    location_match = Column(Float)  # 0-1
    rating_match = Column(Float)  # 0-1

    overall_score = Column(Float, index=True)  # 0-1
    match_reason = Column(Text)

    # Status
    status = Column(Enum(MatchStatus), default=MatchStatus.SUGGESTED, index=True)
    worker_response = Column(String, nullable=True)  # "accepted", "rejected"
    worker_responded_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_job_score', 'job_id', 'overall_score'),
        Index('idx_worker_status', 'worker_id', 'status'),
    )


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), index=True)
    approval_type = Column(String)  # "registration", "job_application"

    # AI Decision
    ai_score = Column(Float)  # 0-100
    ai_decision = Column(Enum(ApprovalDecision))
    ai_reasoning = Column(Text)
    ai_factors = Column(JSON)  # {"email_verified": true, "experience": 5, ...}

    # Admin Override
    admin_decision = Column(String, nullable=True)  # "approved", "rejected"
    admin_notes = Column(Text, nullable=True)
    approved_by = Column(String, nullable=True)
    admin_decided_at = Column(DateTime, nullable=True)

    # Final Status
    status = Column(String, default="pending", index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_type = Column(String, index=True)  # "demand", "pricing", "churn"
    entity_type = Column(String)  # "category", "worker", "location"
    entity_id = Column(Integer, nullable=True)

    # Data
    metric = Column(String)  # "job_volume", "avg_rate", "churn_probability"
    value = Column(Float)
    forecast_period = Column(String)  # "7days", "30days", "90days"
    confidence = Column(Float)  # 0-1

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)


class WorkerActivityLog(Base):
    __tablename__ = "worker_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), index=True)
    action = Column(String)  # "registered", "applied", "completed_job"
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
