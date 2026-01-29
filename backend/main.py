from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from core.config import settings

# Create FastAPI application
app = FastAPI(
    title="PDF Translation API with XLIFF Reflow",
    description="Translate PDFs while preserving layout using Apryse + DeepL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["PDF Operations"])
print(f"✓ Router included with {len(router.routes)} routes")
for route in router.routes:
    print(f"  - {route.methods} {route.path}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "PDF Translation API with XLIFF Reflow",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "PDF Upload & Validation",
            "Text Extraction with Positions",
            "XLIFF-based Translation with DeepL",
            "Layout Preservation using Apryse Reflow",
            "Pre/Post Translation Editing Support",
            "Download Original & Translated PDFs"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "PDF Translation API is running",
        "temp_dir": settings.TEMP_DIR,
        "apryse_configured": bool(settings.APRYSE_LICENSE_KEY),
        "deepl_configured": bool(settings.DEEPL_API_KEY)
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("  PDF Translation System with Layout Preservation")
    print("  Powered by Apryse XLIFF Reflow + DeepL Translation")
    print("="*70)
    print(f"\n  🚀 Starting server...")
    print(f"  📁 Temp Directory: {settings.TEMP_DIR}")
    # print(f"  🔑 Apryse License: {'✓ Configured' if settings.APRYSE_LICENSE_KEY else '✗ Missing'}")
    print(f"  🔑 DeepL API Key: {'✓ Configured' if settings.DEEPL_API_KEY else '✗ Missing'}")
    print(f"\n  📖 API Documentation: http://localhost:8001/docs")
    print(f"  🏥 Health Check: http://localhost:8001/health")
    print(f"\n" + "="*70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
