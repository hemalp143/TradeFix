from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# Enums
class SubscriptionTierEnum(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Worker Schemas
class WorkerRegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    postal_code: str = Field(..., min_length=6, max_length=10)
    latitude: float
    longitude: float
    skills: List[str] = Field(default=[], max_items=10)
    experience_years: int = Field(default=0, ge=0, le=70)
    hourly_rate: float = Field(default=0.0, ge=0)
    bio: Optional[str] = None
    subscription_tier: SubscriptionTierEnum = SubscriptionTierEnum.STARTER
    availability: Optional[Dict] = None


class WorkerUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    hourly_rate: Optional[float] = None
    bio: Optional[str] = None
    availability: Optional[Dict] = None


class WorkerResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    postal_code: str
    latitude: float
    longitude: float
    skills: List[str]
    experience_years: int
    hourly_rate: float
    bio: Optional[str]
    subscription_tier: str
    subscription_status: str
    approval_status: str
    approval_score: float
    rating: float
    matched_jobs: int
    completion_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


# Job Schemas
class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    category: str
    required_skills: List[str] = Field(default=[], max_items=10)
    experience_required: int = Field(default=0, ge=0)
    pay_rate: float = Field(..., gt=0)
    duration_hours: float = Field(..., gt=0)
    postal_code: str
    latitude: float
    longitude: float
    radius: float = 25.0
    scheduled_date: datetime
    scheduled_time: str  # "09:00-17:00"
    deadline: datetime
    priority: str = "medium"
    client_id: int
    client_name: str


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    required_skills: List[str]
    experience_required: int
    pay_rate: float
    duration_hours: float
    postal_code: str
    latitude: float
    longitude: float
    status: str
    priority: str
    client_name: str
    client_rating: float
    matched_workers: List[Dict]
    assigned_worker_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Matching Schemas
class MatchingRequest(BaseModel):
    job_id: int
    top_n: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.65, ge=0, le=1)


class MatchResponse(BaseModel):
    worker_id: int
    job_id: int
    skills_match: float
    experience_match: float
    availability_match: float
    location_match: float
    rating_match: float
    overall_score: float
    reasoning: str
    meets_minimum: bool


class BulkMatchRequest(BaseModel):
    job_ids: List[int] = Field(..., max_items=100)
    top_n: int = Field(default=3, ge=1, le=20)
    min_score: float = Field(default=0.65, ge=0, le=1)


# Approval Schemas
class ApprovalResponse(BaseModel):
    worker_id: int
    email: str
    score: float
    decision: str
    reasoning: str
    factors: Dict


class AutoApprovalRequest(BaseModel):
    worker_ids: List[int] = Field(..., max_items=100)


class ApprovalOverrideRequest(BaseModel):
    approval_id: int
    decision: str = Field(..., regex="^(approved|rejected)$")
    notes: Optional[str] = None
    admin_id: str


# Analytics Schemas
class DemandForecast(BaseModel):
    period: str  # "7days", "30days", "90days"
    metric: str  # "job_volume", "avg_rate"
    forecast_value: float
    confidence: float
    category: Optional[str] = None


class RevenueStats(BaseModel):
    total_revenue: float
    active_subscriptions: int
    avg_subscription_value: float
    period: str


class WorkerStats(BaseModel):
    total_workers: int
    active_workers: int
    approved_workers: int
    pending_approvals: int
    avg_rating: float
    total_matched_jobs: int


# Error Response
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
