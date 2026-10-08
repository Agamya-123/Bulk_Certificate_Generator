from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app.database import close_db, init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure storage folders exist and initialize DB tables
    settings.init_storage()
    await init_db()
    yield
    # Shutdown: clean up DB connections
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# Bulk Certificate Generator API & Web Application

High-performance, fault-tolerant backend service & modern web application to generate, track, and distribute verified certificates in bulk.

## Features
* **Interactive Web Application**: Responsive single-page web app with drag-and-drop CSV ingestion, live progress monitor, and public verification portal.
* **Bulk Asynchronous Processing**: Accept thousands of recipients in a single request and generate certificates in parallel.
* **Fault-Tolerant Generation**: Individual recipient failures do not abort the generation of remaining valid certificates.
* **Real-time Progress Tracking**: Track generation progress (percentage, success/fail counts, individual certificate status).
* **High-Fidelity PDF Engine**: Vector-rendered, print-ready landscape certificates with customizable branding and dynamic layout scaling.
* **Bulk & Individual Retrieval**: Download single PDFs or all certificates packaged in a ZIP archive.
* **Public Certificate Verification**: Cryptographic certificate codes with public authenticity verification.
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["Frontend"], summary="Web Application SPA")
async def root():
    """Serves the frontend Single-Page Application (SPA)."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "health": f"{settings.API_V1_STR}/health",
            "create_job": f"{settings.API_V1_STR}/jobs",
            "list_jobs": f"{settings.API_V1_STR}/jobs",
            "verify_certificate": f"{settings.API_V1_STR}/certificates/verify/{{code}}",
        },
    }


# Mount API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred during request processing.",
        },
    )
