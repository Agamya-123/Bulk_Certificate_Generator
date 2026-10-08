# Bulk Certificate Generator Backend API

A high-performance, fault-tolerant asynchronous REST API built with **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **ReportLab** to generate, track, verify, and distribute high-fidelity certificates in bulk for events, courses, and workshops.

---

## Key Features

- **Bulk Asynchronous Processing**: Accept batches of hundreds or thousands of recipients in a single request without blocking the API client or server event loop.
- **Fault-Tolerant Execution**: A rendering or data failure for one recipient is isolated and recorded without stopping or aborting valid certificates in the batch.
- **Real-Time Progress & Status Tracking**: Live metrics including `processed_count`, `success_count`, `failed_count`, and `progress_percentage`.
- **Landscape Vector PDF Generation**: Predefined certificate template featuring dual navy/gold borders, ornamental rosette seal, dynamic font scaling to prevent text clipping, issuance dates, and unique verification codes.
- **Dual Retrieval Options**:
  - Download individual certificate PDFs via `/api/v1/certificates/{id}/download`.
  - Download all successfully generated certificates bundled in an organized `.zip` archive via `/api/v1/jobs/{id}/download-zip`.
- **Public Certificate Verification**: Public endpoint (`/api/v1/certificates/verify/{code}`) allowing third parties and employers to verify certificate authenticity and recipient credentials.
- **Automated Test Suite**: 100% passing pytest suite covering input validation, background worker execution, fault tolerance, downloads, and verification.

---

## Project Structure

```
bulk_certificate_generator/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── certificates.py    # Individual certificate retrieval & public verification
│   │       ├── health.py          # System health check endpoint
│   │       ├── jobs.py            # Bulk job creation, status, pagination, and ZIP export
│   │       └── router.py          # API v1 router aggregator
│   ├── models/
│   │   ├── certificate.py         # SQLAlchemy model for Certificate (SUCCESS/FAILED/PENDING)
│   │   └── job.py                 # SQLAlchemy model for Job with progress counters & statuses
│   ├── schemas/
│   │   ├── certificate.py         # Pydantic schemas (RecipientInput, CertificateResponse, etc.)
│   │   ├── common.py              # PaginatedResponse[T], MessageResponse
│   │   └── job.py                 # JobCreateRequest, JobDetailResponse, JobSummaryResponse
│   ├── services/
│   │   ├── generator.py           # ReportLab vector PDF rendering engine with dynamic font scaling
│   │   ├── job_service.py         # High-level database queries, CRUD, and verification business logic
│   │   ├── processor.py           # Fault-tolerant background worker with ThreadPoolExecutor
│   │   └── zip_service.py         # In-memory and disk-based ZIP compression service
│   ├── utils/
│   │   ├── file_manager.py        # Safe path resolution and cleanup utilities
│   │   └── security.py            # Certificate code & verification hash generators
│   ├── config.py                  # Pydantic Settings (environment variables, storage paths, limits)
│   ├── database.py                # Async engine, session maker, and table initializers
│   └── main.py                    # FastAPI application, CORS, lifespan, and exception handlers
├── tests/
│   ├── conftest.py                # Async test fixtures, in-memory SQLite, isolated storage
│   ├── test_failure_handling.py   # Partial completion and error capture tests
│   ├── test_generator.py          # PDF layout, header, and long text handling tests
│   ├── test_jobs.py               # Job lifecycle, listing, filtering, and deletion tests
│   ├── test_retrieval.py          # PDF download and bulk ZIP extraction tests
│   ├── test_status_progress.py    # Background execution and progress tracking tests
│   ├── test_validation.py         # Input validation constraints and email verification tests
│   └── test_verification.py       # Public certificate verification tests
├── storage/                       # Local filesystem storage for certificates and ZIP archives
├── pyproject.toml                 # Pytest configuration and metadata
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Testing & linting dependencies
├── run.py                         # Application runner script
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python**: 3.11, 3.12, or 3.13
- **Git** (optional)
- **Virtual Environment tool**: `venv`

---

### Installation & Setup

1. **Clone or Navigate to the Repository Directory**:
   ```bash
   cd bulk_certificate_generator
   ```

2. **Create and Activate a Virtual Environment**:
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell / Command Prompt)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configuration (Environment Variables)**:
   The application uses sensible defaults that work out-of-the-box. You can customize them by creating a `.env` file in the root directory:
   ```env
   PROJECT_NAME="Bulk Certificate Generator API"
   DEBUG=True
   DATABASE_URL="sqlite+aiosqlite:///./bulk_certificates.sqlite3"
   MAX_BATCH_SIZE=10000
   PDF_WORKER_THREADS=4
   DEFAULT_ORGANIZATION="Tech Excellence Institute"
   ```

---

## Running the Application

Start the development server using either `run.py` or `uvicorn`:

```bash
python run.py
```
*or*
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## Running Automated Tests

Run the complete test suite with coverage reporting:

```bash
pytest
```

To run a specific test file or see detailed output:
```bash
pytest -v -s tests/test_failure_handling.py
```

---

## API Usage & Examples

### 1. Submit a Bulk Certificate Generation Request

Submit a list of recipients along with event and issuer details. The request responds immediately with `202 Accepted` and kicks off generation in the background.

**Endpoint:** `POST /api/v1/jobs`

#### cURL Example:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Full-Stack Web Development Bootcamp",
    "event_name": "Full-Stack Web Development Mastery",
    "issue_date": "October 8, 2026",
    "issuer_name": "Dr. Sarah Connor",
    "issuer_title": "Head of Engineering",
    "organization": "Tech Excellence Institute",
    "description": "For successfully completing 120 hours of intensive coursework in distributed systems and modern web architecture.",
    "recipients": [
      {
        "name": "Alice Wonderland",
        "email": "alice@example.com",
        "identifier": "STU-001",
        "custom_data": {"grade": "Distinction", "track": "Frontend"}
      },
      {
        "name": "Bob Builder",
        "email": "bob@example.com",
        "identifier": "STU-002",
        "custom_data": {"grade": "Merit", "track": "Backend"}
      },
      {
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "identifier": "STU-003"
      }
    ]
  }'
```

#### Response (`202 Accepted`):
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "PENDING",
  "total_recipients": 3,
  "message": "Generation job accepted for 3 recipients. Processing started in background.",
  "status_url": "/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "download_zip_url": "/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/download-zip"
}
```

---

### 2. Check Job Status & Progress

Poll the job status endpoint to track live progress and view the status of each certificate.

**Endpoint:** `GET /api/v1/jobs/{job_id}`

#### cURL Example:
```bash
curl "http://localhost:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
```

#### Response (`200 OK`):
```json
{
  "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "title": "Full-Stack Web Development Bootcamp",
  "event_name": "Full-Stack Web Development Mastery",
  "status": "COMPLETED",
  "total_count": 3,
  "processed_count": 3,
  "success_count": 3,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-08T14:30:00Z",
  "completed_at": "2026-10-08T14:30:02Z",
  "download_zip_url": "/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/download-zip",
  "certificates": [
    {
      "id": "e4eaaaf2-7642-11f0-8c9e-525400123456",
      "recipient_name": "Alice Wonderland",
      "recipient_email": "alice@example.com",
      "recipient_identifier": "STU-001",
      "certificate_code": "CERT-2026-A8F2-9C1D",
      "status": "SUCCESS",
      "file_size_bytes": 142850,
      "download_url": "/api/v1/certificates/e4eaaaf2-7642-11f0-8c9e-525400123456/download",
      "verify_url": "/api/v1/certificates/verify/CERT-2026-A8F2-9C1D"
    }
  ]
}
```

---

### 3. Retrieve Generated Certificates

#### Option A: Bulk ZIP Archive Download
Downloads an organized ZIP containing all successful certificates:
```bash
curl -OJ "http://localhost:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/download-zip"
```

#### Option B: Individual Certificate PDF Download
Downloads an individual certificate PDF by certificate ID:
```bash
curl -OJ "http://localhost:8000/api/v1/certificates/e4eaaaf2-7642-11f0-8c9e-525400123456/download"
```

---

### 4. Public Certificate Verification

Verify authenticity and details without authentication:

**Endpoint:** `GET /api/v1/certificates/verify/{certificate_code}`

#### cURL Example:
```bash
curl "http://localhost:8000/api/v1/certificates/verify/CERT-2026-A8F2-9C1D"
```

#### Response:
```json
{
  "valid": true,
  "certificate_code": "CERT-2026-A8F2-9C1D",
  "status": "SUCCESS",
  "recipient_name": "Alice Wonderland",
  "recipient_email": "alice@example.com",
  "recipient_identifier": "STU-001",
  "event_name": "Full-Stack Web Development Mastery",
  "organization": "Tech Excellence Institute",
  "issue_date": "October 8, 2026",
  "issuer_name": "Dr. Sarah Connor",
  "issuer_title": "Head of Engineering",
  "issued_at": "2026-10-08T14:30:01Z",
  "verification_hash": "a4f89d...",
  "message": "Certificate CERT-2026-A8F2-9C1D is authentic and valid."
}
```

---

## Implementation & Design Decisions

### 1. Asynchronous Background Processing
- **Problem**: Generating high-resolution vector PDFs with ReportLab is CPU-bound. If executed synchronously inside the HTTP request handler, requests with 100+ recipients would block the event loop and cause HTTP gateway timeouts.
- **Solution**: The API accepts the batch payload, validates schema constraints, stores `Job` and `Certificate` database records in `PENDING` status, and responds immediately with `202 Accepted`. A background task handles generation using a `ThreadPoolExecutor` with worker threads (`PDF_WORKER_THREADS`), ensuring the async event loop remains responsive for incoming traffic.

### 2. Fault Tolerance & Isolated Failures
- **Problem**: An invalid recipient attribute, font corruption, or file-system error for one recipient should not fail the entire batch.
- **Solution**: The generator wraps each recipient's rendering in an isolated `try/except` block.
  - If a certificate fails, its database record is marked as `FAILED`, the specific error message is recorded, and the job's `failed_count` is incremented.
  - The remaining valid certificates continue generating normally.
  - The overall job status transitions to `COMPLETED` (if all succeed), `PARTIALLY_COMPLETED` (if some succeed and some fail), or `FAILED` (if all fail).
  - The bulk ZIP packaging only includes successfully generated certificates.

### 3. Vector-Based PDF Rendering & Dynamic Typography
- **Problem**: Long recipient names or event titles often overflow or clip when rendered on fixed templates.
- **Solution**: The `CertificateGenerator` dynamically measures text dimensions (`canvas.stringWidth`) against printable boundaries and scales down font sizes gracefully.
- All elements (borders, security rosettes, ribbon accents, and typography) are drawn as crisp vector primitives using ReportLab, ensuring fast rendering speeds (~10-20ms per certificate) and small file footprints (~100-150 KB).

### 4. Database & Transaction Architecture
- **SQLAlchemy 2.0 Async ORM**: Native `async`/`await` support using `aiosqlite` for lightweight embedded persistence or `asyncpg` for PostgreSQL.
- **Data Integrity**: Foreign key constraints with `ondelete="CASCADE"` ensure clean cascading deletions when removing a job.
- **Live Progress Updates**: Counters are updated after each certificate item finishes, providing real-time progress percentages to polling clients.

---

## License

MIT License. Designed and implemented for high-reliability bulk certificate workflows.
