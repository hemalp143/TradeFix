import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.config import settings
from app.database import get_db, init_db
from app.models import Worker, Job, Match, Approval, ApprovalStatus
from app.schemas import (
    WorkerRegisterRequest, WorkerResponse, WorkerUpdateRequest,
    JobCreateRequest, JobResponse,
    MatchingRequest, MatchResponse,
    ApprovalResponse, AutoApprovalRequest, ApprovalOverrideRequest,
    DemandForecast, WorkerStats, RevenueStats, ErrorResponse
)
from ai.matcher import JobWorkerMatcher
from ai.approval_engine import AutoApprovalEngine, ApprovalRulesEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered worker marketplace"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI engines
matcher = JobWorkerMatcher()
approval_engine = AutoApprovalEngine()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_name}


# ============================================================================
# WORKER ENDPOINTS
# ============================================================================

@app.post("/api/v1/workers/register", response_model=dict)
async def register_worker(
    request: WorkerRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new worker.

    AI automatically evaluates application for approval.
    """
    try:
        # Check duplicate email
        existing = db.query(Worker).filter(Worker.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create worker record
        worker = Worker(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            postal_code=request.postal_code,
            latitude=request.latitude,
            longitude=request.longitude,
            skills=request.skills,
            experience_years=request.experience_years,
            hourly_rate=request.hourly_rate,
            bio=request.bio,
            subscription_tier=request.subscription_tier,
            availability=request.availability or {},
        )

        # Auto-evaluate for approval
        score, decision, reasoning, factors = approval_engine.evaluate_worker(worker)

        worker.approval_score = score
        worker.approval_status = ApprovalStatus.APPROVED if decision.value == "auto_approve" else ApprovalStatus.PENDING

        db.add(worker)
        db.commit()
        db.refresh(worker)

        # Create approval record
        approval = Approval(
            worker_id=worker.id,
            approval_type="registration",
            ai_score=score,
            ai_decision=decision,
            ai_reasoning=reasoning,
            ai_factors=factors,
            status="pending" if decision.value == "manual_review" else decision.value
        )
        db.add(approval)
        db.commit()

        logger.info(f"Worker {worker.id} registered with approval score {score}")

        return {
            "success": True,
            "worker_id": worker.id,
            "email": worker.email,
            "approval_status": worker.approval_status,
            "approval_score": score,
            "message": reasoning
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering worker: {e}")
        raise HTTPException(status_code=500, detail="Failed to register worker")


@app.get("/api/v1/workers/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: int, db: Session = Depends(get_db)):
    """Get worker details."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@app.put("/api/v1/workers/{worker_id}")
async def update_worker(
    worker_id: int,
    request: WorkerUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update worker profile."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Update fields if provided
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)

    db.commit()
    db.refresh(worker)

    return {"success": True, "worker": WorkerResponse.from_orm(worker)}


@app.get("/api/v1/workers")
async def list_workers(
    status: str = None,
    tier: str = None,
    postal_code: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List workers with filters."""
    query = db.query(Worker)

    if status:
        query = query.filter(Worker.approval_status == status)
    if tier:
        query = query.filter(Worker.subscription_tier == tier)
    if postal_code:
        query = query.filter(Worker.postal_code == postal_code)

    workers = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "total": total,
        "workers": [WorkerResponse.from_orm(w) for w in workers]
    }


# ============================================================================
# JOB ENDPOINTS
# ============================================================================

@app.post("/api/v1/jobs", response_model=dict)
async def create_job(request: JobCreateRequest, db: Session = Depends(get_db)):
    """Create a new job (AI extracts skills and estimates completion time)."""
    try:
        job = Job(
            title=request.title,
            description=request.description,
            category=request.category,
            required_skills=request.required_skills,
            experience_required=request.experience_required,
            pay_rate=request.pay_rate,
            duration_hours=request.duration_hours,
            postal_code=request.postal_code,
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
            deadline=request.deadline,
            priority=request.priority,
            client_id=request.client_id,
            client_name=request.client_name,
            estimated_completion_time=request.duration_hours
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Job {job.id} created: {job.title}")

        return {
            "success": True,
            "job_id": job.id,
            "title": job.title,
            "message": "Job created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/v1/jobs")
async def list_jobs(
    status: str = None,
    postal_code: str = None,
    category: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List jobs with filters."""
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if postal_code:
        query = query.filter(Job.postal_code == postal_code)
    if category:
        query = query.filter(Job.category == category)

    jobs = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "total": total,
        "jobs": [JobResponse.from_orm(j) for j in jobs]
    }


# ============================================================================
# MATCHING ENDPOINTS
# ============================================================================

@app.post("/api/v1/matching/find-workers")
async def find_workers_for_job(
    request: MatchingRequest,
    db: Session = Depends(get_db)
):
    """Find best workers for a job using AI matching."""
    try:
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get candidate workers (active, in postal code, approved)
        candidates = db.query(Worker).filter(
            Worker.approval_status == ApprovalStatus.APPROVED,
            Worker.subscription_status == "active",
            Worker.postal_code == job.postal_code  # Can expand to radius
        ).all()

        if not candidates:
            return {"job_id": job.id, "matches": [], "message": "No suitable workers found"}

        # Run matching algorithm
        matches = matcher.find_best_workers_for_job(
            job, candidates, top_n=request.top_n, min_score=request.min_score
        )

        # Save matches to database
        for match_data in matches:
            match = Match(
                job_id=job.id,
                worker_id=match_data['worker_id'],
                skills_match=match_data['skills_match'],
                experience_match=match_data['experience_match'],
                availability_match=match_data['availability_match'],
                location_match=match_data['location_match'],
                rating_match=match_data['rating_match'],
                overall_score=match_data['overall_score'],
                match_reason=match_data['reasoning']
            )
            db.add(match)

        db.commit()

        logger.info(f"Found {len(matches)} matches for job {job.id}")

        return {
            "job_id": job.id,
            "job_title": job.title,
            "matches": matches,
            "total_matches": len(matches)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding workers: {e}")
        raise HTTPException(status_code=500, detail="Matching failed")


@app.post("/api/v1/matching/find-jobs")
async def find_jobs_for_worker(
    worker_id: int,
    top_n: int = 5,
    min_score: float = 0.65,
    db: Session = Depends(get_db)
):
    """Find best jobs for a worker using AI matching."""
    try:
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        # Get open jobs in area
        candidates = db.query(Job).filter(
            Job.status == "open",
            Job.postal_code == worker.postal_code
        ).all()

        if not candidates:
            return {"worker_id": worker_id, "jobs": [], "message": "No suitable jobs found"}

        # Run matching algorithm
        matches = matcher.find_best_jobs_for_worker(
            worker, candidates, top_n=top_n, min_score=min_score
        )

        return {
            "worker_id": worker_id,
            "worker_name": f"{worker.first_name} {worker.last_name}",
            "jobs": matches,
            "total_jobs": len(matches)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding jobs: {e}")
        raise HTTPException(status_code=500, detail="Matching failed")


# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@app.post("/api/v1/approvals/auto-process")
async def auto_process_approvals(
    request: AutoApprovalRequest,
    db: Session = Depends(get_db)
):
    """Auto-process pending approvals for workers."""
    try:
        workers = db.query(Worker).filter(Worker.id.in_(request.worker_ids)).all()

        auto_approve, manual_review = approval_engine.auto_approve_eligible_workers(workers)

        # Update auto-approved workers
        for item in auto_approve:
            item['worker'].approval_status = ApprovalStatus.APPROVED
            item['worker'].subscription_status = "active"

        db.commit()

        logger.info(f"Auto-processed {len(auto_approve)} approvals, {len(manual_review)} for review")

        return {
            "auto_approved": len(auto_approve),
            "manual_review": len(manual_review),
            "auto_approved_workers": [w['worker'].email for w in auto_approve],
            "manual_review_details": [
                {
                    "worker_id": w['worker'].id,
                    "email": w['worker'].email,
                    "score": w['score'],
                    "reason": w['reasoning']
                }
                for w in manual_review
            ]
        }

    except Exception as e:
        logger.error(f"Error auto-processing approvals: {e}")
        raise HTTPException(status_code=500, detail="Approval processing failed")


@app.get("/api/v1/approvals/pending")
async def list_pending_approvals(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List pending approvals."""
    approvals = db.query(Approval).filter(
        Approval.status == "pending"
    ).offset(skip).limit(limit).all()

    total = db.query(Approval).filter(Approval.status == "pending").count()

    return {
        "total": total,
        "approvals": [
            {
                "id": a.id,
                "worker_id": a.worker_id,
                "score": a.ai_score,
                "decision": a.ai_decision.value if a.ai_decision else None,
                "reasoning": a.ai_reasoning,
                "factors": a.ai_factors
            }
            for a in approvals
        ]
    }


@app.post("/api/v1/approvals/{approval_id}/override")
async def override_approval(
    approval_id: int,
    request: ApprovalOverrideRequest,
    db: Session = Depends(get_db)
):
    """Admin override approval decision."""
    try:
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")

        # Update approval
        approval.admin_decision = request.decision
        approval.admin_notes = request.notes
        approval.approved_by = request.admin_id
        approval.status = request.decision

        # Update worker
        worker = db.query(Worker).filter(Worker.id == approval.worker_id).first()
        if request.decision == "approved":
            worker.approval_status = ApprovalStatus.APPROVED
            worker.subscription_status = "active"
        else:
            worker.approval_status = ApprovalStatus.REJECTED

        db.commit()

        logger.info(f"Admin override approval {approval_id}: {request.decision}")

        return {
            "success": True,
            "approval_id": approval_id,
            "decision": request.decision,
            "message": "Approval overridden"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding approval: {e}")
        raise HTTPException(status_code=500, detail="Override failed")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/analytics/workers")
async def worker_analytics(db: Session = Depends(get_db)):
    """Get worker statistics."""
    total = db.query(Worker).count()
    active = db.query(Worker).filter(Worker.subscription_status == "active").count()
    approved = db.query(Worker).filter(Worker.approval_status == ApprovalStatus.APPROVED).count()
    pending = db.query(Worker).filter(Worker.approval_status == ApprovalStatus.PENDING).count()

    # Calculate averages
    from sqlalchemy import func
    avg_rating_result = db.query(func.avg(Worker.rating)).scalar()
    total_matched = db.query(func.sum(Worker.matched_jobs)).scalar()

    return WorkerStats(
        total_workers=total,
        active_workers=active,
        approved_workers=approved,
        pending_approvals=pending,
        avg_rating=float(avg_rating_result or 0),
        total_matched_jobs=int(total_matched or 0)
    )


@app.get("/api/v1/analytics/jobs")
async def job_analytics(db: Session = Depends(get_db)):
    """Get job statistics."""
    total = db.query(Job).count()
    open_jobs = db.query(Job).filter(Job.status == "open").count()
    assigned = db.query(Job).filter(Job.status == "assigned").count()
    completed = db.query(Job).filter(Job.status == "completed").count()

    return {
        "total_jobs": total,
        "open_jobs": open_jobs,
        "assigned_jobs": assigned,
        "completed_jobs": completed
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
