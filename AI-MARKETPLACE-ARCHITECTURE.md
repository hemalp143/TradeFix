# AI-Powered Worker Marketplace - System Architecture

## Overview
Complete AI/automation system for intelligent job-to-worker matching, predictive analytics, and automated approval workflows.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface                            │
│  (manage workers, jobs, approvals, analytics)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend                             │
│  (REST API for workers, jobs, matching, predictions)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────────┐ ┌──▼──────────┐ ┌─▼──────────────┐
│   PostgreSQL   │ │   Redis     │ │  Celery Queue  │
│   Database     │ │   Cache     │ │  (Async Jobs)  │
└────────────────┘ └─────────────┘ └────────────────┘
        │
┌───────▼──────────────────────────────────────────┐
│         AI/ML Services (Python)                  │
│ ┌─────────────────────────────────────────────┐  │
│ │ • Worker-Job Matching (embeddings/cosine)  │  │
│ │ • Auto-Approval Engine (classification)    │  │
│ │ • Predictive Analytics (demand, pricing)   │  │
│ │ • NLP Processing (profile extraction)      │  │
│ │ • Skill Extraction (skills detection)      │  │
│ └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

---

## Project Structure

```
ai-worker-marketplace/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── models.py               # Database models
│   │   ├── database.py             # DB connection
│   │   ├── api/
│   │   │   ├── workers.py          # Worker endpoints
│   │   │   ├── jobs.py             # Job endpoints
│   │   │   ├── matching.py         # Matching API
│   │   │   ├── predictions.py      # Analytics API
│   │   │   └── approvals.py        # Approval endpoints
│   │   └── schemas/
│   │       ├── worker.py
│   │       ├── job.py
│   │       └── matching.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── matcher.py              # Job-worker matching
│   │   ├── approval_engine.py      # Auto-approval logic
│   │   ├── predictor.py            # Demand/pricing predictions
│   │   ├── nlp_processor.py        # NLP & skill extraction
│   │   └── embeddings.py           # Vector embeddings
│   │
│   ├── tasks/
│   │   ├── celery.py               # Celery config
│   │   ├── matching_tasks.py       # Async matching jobs
│   │   ├── approval_tasks.py       # Async approvals
│   │   └── analytics_tasks.py      # Analytics processing
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── cache.py
│   │   └── validators.py
│   │
│   ├── tests/
│   │   ├── test_matching.py
│   │   ├── test_approvals.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── docker-compose.yml
│
├── cli/
│   ├── __init__.py
│   ├── cli.py                      # Main CLI entry point
│   ├── commands/
│   │   ├── workers.py              # worker commands
│   │   ├── jobs.py                 # job commands
│   │   ├── matching.py             # matching commands
│   │   ├── approvals.py            # approval commands
│   │   └── analytics.py            # analytics commands
│   │
│   └── utils/
│       ├── formatters.py
│       └── table.py
│
├── scripts/
│   ├── init_db.py                  # Initialize database
│   ├── seed_data.py                # Seed test data
│   └── train_models.py             # Train ML models
│
├── docs/
│   ├── API.md
│   ├── CLI-GUIDE.md
│   ├── AI-MODELS.md
│   └── DEPLOYMENT.md
│
├── docker-compose.yml
├── Dockerfile
├── README.md
└── .gitignore
```

---

## Database Schema

### Workers Table
```python
class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    
    # Location
    postal_code = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Profile
    skills = Column(JSON)  # ["plumbing", "gas fitting", "emergency repairs"]
    experience_years = Column(Integer)
    hourly_rate = Column(Float)
    availability = Column(JSON)  # {"mon": [9,17], "tue": [9,17]}
    bio = Column(Text)
    
    # Subscription
    subscription_tier = Column(Enum("starter", "professional", "enterprise"))
    subscription_status = Column(Enum("active", "inactive", "suspended"))
    subscription_start = Column(DateTime)
    subscription_end = Column(DateTime)
    
    # Status
    approval_status = Column(Enum("pending", "approved", "rejected", "suspended"))
    approval_score = Column(Float)  # AI approval score (0-100)
    matched_jobs = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # % of completed jobs
    rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    embedding = Column(LargeBinary)  # Vector embedding for matching
```

### Jobs Table
```python
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String, index=True)  # "plumbing", "electrical", etc.
    
    # Requirements
    required_skills = Column(JSON)  # ["plumbing", "emergency response"]
    experience_required = Column(Integer)  # years
    pay_rate = Column(Float)
    duration_hours = Column(Float)
    
    # Location
    postal_code = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float)  # miles
    
    # Timeline
    scheduled_date = Column(DateTime)
    scheduled_time = Column(String)  # "09:00-17:00"
    deadline = Column(DateTime)
    
    # Status
    status = Column(Enum("open", "matched", "assigned", "in_progress", "completed", "cancelled"))
    priority = Column(Enum("low", "medium", "high", "urgent"))
    
    # Client
    client_id = Column(Integer, ForeignKey("clients.id"))
    client_name = Column(String)
    client_rating = Column(Float)
    
    # Matching
    matched_workers = Column(JSON)  # [{"worker_id": 1, "score": 0.92}, ...]
    assigned_worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    
    # Predictions
    estimated_completion_time = Column(Float)  # hours
    demand_score = Column(Float)  # 0-100, how in-demand this job type is
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    embedding = Column(LargeBinary)  # Vector embedding
```

### Approvals Table
```python
class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    type = Column(Enum("registration", "job_application"))
    
    # AI Decision
    ai_score = Column(Float)  # 0-100
    ai_decision = Column(Enum("auto_approve", "auto_reject", "manual_review"))
    ai_reasoning = Column(Text)  # Why the AI made this decision
    
    # Admin Override
    admin_decision = Column(Enum("approved", "rejected", "pending"))
    admin_notes = Column(Text)
    approved_by = Column(String)
    
    status = Column(Enum("pending", "approved", "rejected"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Matches Table
```python
class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    
    # Matching Score Breakdown
    skills_match = Column(Float)  # 0-1
    experience_match = Column(Float)  # 0-1
    availability_match = Column(Float)  # 0-1
    location_match = Column(Float)  # 0-1
    rating_match = Column(Float)  # 0-1
    
    overall_score = Column(Float)  # 0-1, weighted average
    match_reason = Column(Text)  # Why they matched
    
    status = Column(Enum("suggested", "applied", "accepted", "rejected", "completed"))
    worker_response = Column(Enum("pending", "accepted", "rejected"))
    worker_responded_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Core AI/ML Features

### 1. Intelligent Job-to-Worker Matching

**Algorithm**: Semantic similarity + Multi-factor scoring

```python
# Matching Score = 
# 0.30 * skills_match +
# 0.25 * experience_match +
# 0.20 * availability_match +
# 0.15 * location_distance +
# 0.10 * historical_rating

# Example: 
# Plumber job, needs 5 years exp, £25/hr
# Worker: plumber (match 0.95), 7 years (1.0), available Mon 9-5 (0.8), 2 miles away (0.9), rating 4.8/5 (0.96)
# Score = 0.30*0.95 + 0.25*1.0 + 0.20*0.8 + 0.15*0.9 + 0.10*0.96 = 0.938
```

**Implementation**: 
- Sentence-transformers for skill/job embedding
- Cosine similarity for semantic matching
- Haversine formula for distance calculation
- PostgreSQL vector search (pgvector extension)

### 2. Automated Approval Engine

**Decision Logic**:
```
IF email_verified AND postal_code_valid:
    IF experience_years >= 2 AND rating > 3.0:
        auto_approve with score = 90
    ELIF experience_years >= 1:
        manual_review with score = 65
    ELSE:
        auto_reject with score = 40
```

**Factors**:
- Email verification
- Postal code validity
- Experience level
- Completion history
- Document verification
- Skills validation

### 3. Predictive Analytics

**Demand Forecasting**:
- Time-series analysis (ARIMA) for job volume
- Seasonal patterns detection
- Geographic hotspot identification

**Pricing Optimization**:
- Dynamic pricing based on demand/supply
- Surge pricing for urgent jobs
- Skill-based rate recommendations

**Worker Availability Prediction**:
- Predict worker churn/attrition
- Recommend optimal work hours
- Identify burnout risk

### 4. NLP & Skill Extraction

**Capabilities**:
- Extract skills from job descriptions
- Match extracted skills to worker profiles
- Auto-categorize jobs
- Detect duplicate skills (synonyms)

**Example**:
```
Job description: "Need experienced plumber for emergency gas line repair"
Extracted: ["plumbing", "gas fitting", "emergency response", "repairs"]
Skill mapping: plumber role tags = ["plumbing", "gas_fitting", "emergency"]
Match score: 0.98 (high relevance)
```

---

## CLI Commands

```bash
# Worker Management
cli workers list --status=pending --tier=professional
cli workers approve <worker_id> --notes="Verified credentials"
cli workers suspend <worker_id> --reason="ratings dropped below 3.0"
cli workers view <worker_id>

# Job Management
cli jobs create --title="Plumbing repair" --skills="plumbing,emergency" --pay=50 --location="SW1A 1AA"
cli jobs list --status=open --priority=urgent
cli jobs match <job_id>  # Find best workers for this job
cli jobs assign <job_id> <worker_id>

# Matching & Analytics
cli matching auto-run --min-score=0.80  # Run all pending matches
cli matching show <job_id>  # Show top 5 matched workers
cli matching suggest <job_id>  # AI suggests best matches

# Approvals
cli approvals list --pending
cli approvals auto-process --threshold=80  # Auto-approve score >= 80
cli approvals override <approval_id> --decision=approved

# Analytics
cli analytics workers --stats  # Total, active, suspended, avg rating
cli analytics jobs --forecast=30days  # Demand forecast next 30 days
cli analytics revenue --period=month
cli analytics hotspots  # Geographic demand hotspots

# System
cli system init-db  # Initialize database
cli system seed-data  # Load test data
cli system health  # Check all services running
```

---

## API Endpoints

### Workers
```
POST   /api/workers/register              # Create worker (AI pre-scores)
GET    /api/workers/<id>                  # Get worker details
PUT    /api/workers/<id>                  # Update profile
GET    /api/workers/search?skills=plumbing # Search workers
GET    /api/workers/<id>/approval-status  # Get approval status
```

### Jobs
```
POST   /api/jobs                          # Create job (AI extracts skills)
GET    /api/jobs/<id>                     # Get job details
PUT    /api/jobs/<id>                     # Update job
GET    /api/jobs/search?category=plumbing # Search jobs
GET    /api/jobs/<id>/matches             # Get matched workers
```

### Matching
```
POST   /api/matching/find-workers         # Find best workers for job
POST   /api/matching/find-jobs            # Find best jobs for worker
GET    /api/matching/<job_id>/scores      # Get detailed match scores
POST   /api/matching/explain              # Explain why match happened
```

### Predictions
```
GET    /api/predictions/demand?days=30    # Forecast job demand
GET    /api/predictions/pricing           # Recommended pricing
GET    /api/predictions/worker-capacity   # Worker availability forecast
GET    /api/predictions/completion-time   # Estimated job duration
```

### Approvals
```
GET    /api/approvals/pending             # List pending approvals
POST   /api/approvals/<id>/auto-decide    # Run AI approval logic
POST   /api/approvals/<id>/override       # Admin override decision
GET    /api/approvals/<id>/reasoning      # Why AI made decision
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI (modern, fast, automatic docs)
- **Database**: PostgreSQL 14+ (with pgvector for embeddings)
- **Cache**: Redis (session, caching, rate limiting)
- **Queue**: Celery + RabbitMQ (async task processing)
- **ORM**: SQLAlchemy 2.0

### AI/ML
- **Embeddings**: sentence-transformers (semantic matching)
- **NLP**: spaCy (skill extraction, text processing)
- **Forecasting**: statsmodels (ARIMA for demand)
- **ML**: scikit-learn (approval scoring, classification)
- **Vector DB**: pgvector PostgreSQL extension

### CLI
- **Framework**: Typer (modern CLI with auto-docs)
- **Tables**: Rich (beautiful terminal tables)
- **Formatting**: Pydantic (data validation)

### DevOps
- **Containerization**: Docker + Docker Compose
- **Testing**: pytest + pytest-asyncio
- **Logging**: Python logging + structured logs
- **Monitoring**: OpenTelemetry ready

---

## Development Workflow

### Phase 1: Core Backend (Week 1-2)
- [ ] Setup FastAPI project & database
- [ ] Implement worker/job models
- [ ] Build basic CRUD APIs
- [ ] Setup Redis & Celery

### Phase 2: AI Matching (Week 2-3)
- [ ] Implement semantic embeddings
- [ ] Build matching algorithm
- [ ] Create match scoring logic
- [ ] Test with sample data

### Phase 3: Automation & Approvals (Week 3-4)
- [ ] Build approval engine
- [ ] Create auto-decision logic
- [ ] Implement NLP skill extraction
- [ ] Add approval override system

### Phase 4: Predictions (Week 4-5)
- [ ] Demand forecasting
- [ ] Pricing recommendations
- [ ] Worker analytics
- [ ] Performance dashboards

### Phase 5: CLI Tool (Week 5-6)
- [ ] Implement all CLI commands
- [ ] Build interactive tables
- [ ] Add batch operations
- [ ] Create shell completion

### Phase 6: Testing & Deployment (Week 6-7)
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests
- [ ] Docker deployment
- [ ] Documentation

---

## Ready to Implement?

I can provide complete, production-ready code for:
1. **FastAPI backend** with all models and endpoints
2. **AI matching engine** with similarity scoring
3. **Approval automation** with rules engine
4. **CLI tool** with all commands
5. **Database setup** with seed data
6. **Docker setup** for easy deployment
7. **Tests** and CI/CD configuration

**Next Step**: Shall I start coding the complete backend?
