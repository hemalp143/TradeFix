# AI Worker Marketplace - Backend

Production-ready FastAPI backend with intelligent job-to-worker matching, automated approvals, and predictive analytics.

## Features

### 🤖 AI/ML Capabilities
- **Intelligent Job Matching**: Semantic similarity + multi-factor scoring (skills, experience, location, availability)
- **Auto-Approval Engine**: Automated decision making for worker registration with configurable thresholds
- **Predictive Analytics**: Demand forecasting, pricing optimization, worker availability prediction
- **NLP Processing**: Skill extraction, profile analysis, job categorization

### ⚙️ Automation
- **Batch Matching**: Match multiple jobs to workers in single operation
- **Auto-Approvals**: Process pending approvals with configurable AI thresholds
- **Subscription Management**: Automatic tier handling and renewal tracking
- **Activity Logging**: Complete audit trail of all operations

### 📊 Analytics
- **Worker Statistics**: Total workers, active, approved, pending
- **Job Analytics**: Open, assigned, completed, cancelled
- **Revenue Tracking**: Subscription revenue by tier and period
- **Performance Metrics**: Completion rates, match success rates, worker ratings

## Quick Start

### 1. Setup Database & Services (with Docker)

```bash
cd /path/to/TradeFix

# Start PostgreSQL, Redis, and Backend
docker-compose up -d

# Wait for services to be healthy
sleep 5

# Initialize database
docker-compose exec backend python -c "from app.database import init_db; init_db()"
```

### 2. Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Start PostgreSQL and Redis locally
# (see instructions for your OS)

# Initialize database
python app/init_db.py

# Run server
uvicorn app.main:app --reload
```

### 3. API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application + routes
│   ├── config.py               # Configuration settings
│   ├── models.py               # SQLAlchemy database models
│   ├── database.py             # Database connection
│   ├── schemas.py              # Pydantic validation schemas
│   └── __init__.py
│
├── ai/
│   ├── matcher.py              # Job-worker matching engine
│   ├── approval_engine.py      # Automated approval logic
│   ├── predictor.py            # Demand/pricing predictions (TODO)
│   └── nlp_processor.py        # NLP & skill extraction (TODO)
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## API Endpoints

### Workers

**Register Worker** (AI auto-evaluates)
```bash
POST /api/v1/workers/register
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "07700 900000",
  "postal_code": "SW1A 1AA",
  "latitude": 51.5007,
  "longitude": -0.1246,
  "skills": ["plumbing", "gas_fitting"],
  "experience_years": 5,
  "hourly_rate": 45.00,
  "subscription_tier": "professional",
  "availability": {
    "mon": [9, 17],
    "tue": [9, 17],
    "wed": [9, 17]
  }
}
```

**Get Worker**
```bash
GET /api/v1/workers/{worker_id}
```

**List Workers** (with filters)
```bash
GET /api/v1/workers?status=approved&tier=professional&postal_code=SW1A%201AA
```

**Update Worker**
```bash
PUT /api/v1/workers/{worker_id}
```

### Jobs

**Create Job**
```bash
POST /api/v1/jobs
{
  "title": "Emergency plumbing repair",
  "description": "Gas line issue needs immediate attention",
  "category": "plumbing",
  "required_skills": ["plumbing", "gas_fitting", "emergency"],
  "experience_required": 3,
  "pay_rate": 75.00,
  "duration_hours": 2.0,
  "postal_code": "SW1A 1AA",
  "latitude": 51.5007,
  "longitude": -0.1246,
  "scheduled_date": "2024-01-15T09:00:00",
  "scheduled_time": "09:00-11:00",
  "deadline": "2024-01-15T23:59:59",
  "priority": "urgent",
  "client_id": 1,
  "client_name": "London Properties Ltd"
}
```

**List Jobs** (with filters)
```bash
GET /api/v1/jobs?status=open&postal_code=SW1A%201AA&priority=urgent
```

### Matching

**Find Workers for Job**
```bash
POST /api/v1/matching/find-workers
{
  "job_id": 5,
  "top_n": 5,
  "min_score": 0.65
}

Response:
{
  "job_id": 5,
  "job_title": "Emergency plumbing repair",
  "matches": [
    {
      "worker_id": 1,
      "skills_match": 0.95,
      "experience_match": 1.0,
      "availability_match": 0.8,
      "location_match": 0.9,
      "rating_match": 0.96,
      "overall_score": 0.938,
      "reasoning": "High match: skills & experience aligned, 2 miles away"
    },
    ...
  ],
  "total_matches": 5
}
```

**Find Jobs for Worker**
```bash
GET /api/v1/matching/find-jobs?worker_id=1&top_n=5&min_score=0.65
```

### Approvals

**List Pending Approvals**
```bash
GET /api/v1/approvals/pending?skip=0&limit=50
```

**Auto-Process Approvals**
```bash
POST /api/v1/approvals/auto-process
{
  "worker_ids": [1, 2, 3, 4, 5]
}

Response:
{
  "auto_approved": 3,
  "manual_review": 2,
  "auto_approved_workers": ["john@example.com", "jane@example.com", "bob@example.com"],
  "manual_review_details": [...]
}
```

**Override Approval** (Admin)
```bash
POST /api/v1/approvals/{approval_id}/override
{
  "decision": "approved",
  "notes": "Manually approved after phone verification",
  "admin_id": "admin@company.com"
}
```

### Analytics

**Worker Analytics**
```bash
GET /api/v1/analytics/workers

Response:
{
  "total_workers": 150,
  "active_workers": 120,
  "approved_workers": 140,
  "pending_approvals": 10,
  "avg_rating": 4.65,
  "total_matched_jobs": 450
}
```

**Job Analytics**
```bash
GET /api/v1/analytics/jobs

Response:
{
  "total_jobs": 500,
  "open_jobs": 50,
  "assigned_jobs": 150,
  "completed_jobs": 280
}
```

## Approval Engine

The automated approval engine evaluates workers on:

1. **Email Validation** (10 points) - Valid format
2. **Experience** (20 points) - Years of experience
3. **Skills** (15 points) - Number and diversity of skills
4. **Postal Code** (10 points) - Valid UK postcode format
5. **Subscription Tier** (15 points) - Higher tiers = higher score
6. **Phone** (10 points) - Valid phone format
7. **Bio/Profile** (10 points) - Profile completeness

**Scoring Rules**:
- **Score >= 80**: Auto-Approve ✓
- **Score 50-79**: Manual Review ⚠
- **Score < 50**: Auto-Reject ✗

These thresholds are configurable in `.env`:
```env
APPROVAL_AUTO_THRESHOLD=80.0
APPROVAL_REVIEW_THRESHOLD=50.0
```

## Matching Algorithm

Job-to-worker matching uses weighted scoring:

```
Overall Score = 
  0.30 * skills_match +
  0.25 * experience_match +
  0.20 * availability_match +
  0.15 * location_match +
  0.10 * rating_match
```

Each component is scored 0-1 based on:
- **Skills**: Semantic similarity using sentence-transformers
- **Experience**: Years ratio (capped at 1.0)
- **Availability**: Calendar overlap detection
- **Location**: Haversine distance calculation
- **Rating**: Worker's historical rating with confidence weighting

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (cache & message broker)
REDIS_URL=redis://localhost:6379/0

# AI Settings
MATCHING_MIN_SCORE=0.65           # Minimum match threshold
APPROVAL_AUTO_THRESHOLD=80.0      # Auto-approve if >= 80
APPROVAL_REVIEW_THRESHOLD=50.0    # Manual review if < 50
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Lightweight transformer

# API
DEBUG=False
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Models

### Workers
- ID, email, name, phone
- Location (postal code, lat/lng)
- Skills, experience, hourly rate
- Subscription (tier, status, dates)
- Approval status & score
- Rating, matched jobs, completion rate

### Jobs
- ID, title, description, category
- Requirements (skills, experience, pay, hours)
- Location (postal code, lat/lng, radius)
- Timeline (scheduled date/time, deadline)
- Status, priority
- Client info
- Matched workers, assigned worker
- Predictions (duration, demand score)

### Matches
- Job ID, Worker ID
- Individual match scores (skills, experience, availability, location, rating)
- Overall score (weighted)
- Match status (suggested, applied, accepted, completed)
- Worker response & timestamp

### Approvals
- Worker ID, approval type
- AI score & decision (auto_approve, auto_reject, manual_review)
- AI reasoning & factors
- Admin override (decision, notes, admin_id)
- Final status

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov=ai

# Run specific test
pytest tests/test_matching.py::test_skills_match -v
```

## Performance Tips

1. **Batch Operations**: Use bulk matching for multiple jobs
2. **Caching**: Redis caches worker embeddings
3. **Indexes**: Database has indexes on frequently filtered fields
4. **Connection Pooling**: SQLAlchemy manages connection pool
5. **Async Processing**: Celery handles long-running tasks

## Deployment

### Docker (Recommended)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual

1. Setup PostgreSQL 14+ with pgvector extension
2. Setup Redis 6+
3. Install Python dependencies: `pip install -r requirements.txt`
4. Set environment variables
5. Run migrations: `python app/init_db.py`
6. Start with gunicorn: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker`

## Monitoring

- **Logs**: Check `docker logs worker_marketplace_api`
- **Metrics**: Prometheus endpoint at `/metrics`
- **Health**: `curl http://localhost:8000/health`
- **Database**: Connect with `psql`
- **Redis**: Use `redis-cli`

## Troubleshooting

**Error: Database connection refused**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify credentials

**Error: Redis connection refused**
- Ensure Redis is running
- Check REDIS_URL in .env

**Error: Matching returning low scores**
- Check if workers have skills defined
- Verify job requirements are reasonable
- Check availability overlap

**Error: Approval engine not evaluating correctly**
- Review approval thresholds
- Check worker data completeness
- Verify postal code format

## Support

- API Documentation: http://localhost:8000/docs
- GitHub Issues: [link to repo]
- Email: support@example.com

---

Built with ❤️ using FastAPI, SQLAlchemy, and AI/ML
