from pydantic import BaseModel
from typing import List, Dict, Optional

class TextSegment(BaseModel):
    """Text segment with position information for overlay editing"""
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    segment_id: Optional[str] = None

class UploadResponse(BaseModel):
    """Response after successful PDF upload"""
    session_id: str
    filename: str
    message: str

class ExtractTextResponse(BaseModel):
    """Response with extracted text segments"""
    segments: List[TextSegment]
    total_segments: int

class TranslationRequest(BaseModel):
    """Request for PDF translation"""
    source_lang: str
    target_lang: str
    manual_edits: Optional[Dict[str, str]] = None

class TranslationResponse(BaseModel):
    """Response after translation attempt"""
    success: bool
    message: str
    pdf_url: Optional[str] = None
    error: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
