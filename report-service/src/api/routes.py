"""
API Routes for Report Service
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from ..services.report_generator import ReportGenerator, ReportMetadata
from ..services.s3_service import S3Service


router = APIRouter()

# Initialize services
report_generator = ReportGenerator()
s3_service = S3Service()


class GenerateReportRequest(BaseModel):
    """Request model for report generation"""
    user_id: str
    user_name: str
    session_id: str
    workout_data: Dict
    historical_data: Optional[List[Dict]] = None
    ai_insights: Optional[str] = None


class ReportResponse(BaseModel):
    """Response model for report"""
    report_id: str
    user_id: str
    session_id: str
    generated_at: str
    download_url: str
    expires_in: int


@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: GenerateReportRequest):
    """
    Generate workout report PDF

    Args:
        user_id: User identifier
        user_name: User's display name
        session_id: Workout session ID
        workout_data: Current workout session data
        historical_data: Optional historical workout sessions
        ai_insights: Optional AI-generated insights

    Returns:
        Report metadata with download URL
    """
    try:
        # Create report metadata
        metadata = ReportMetadata(
            user_id=request.user_id,
            session_id=request.session_id,
            report_type="workout",
        )

        # Generate PDF
        pdf_buffer = report_generator.generate_workout_report(
            user_name=request.user_name,
            workout_data=request.workout_data,
            historical_data=request.historical_data,
            ai_insights=request.ai_insights,
        )

        # Upload to S3
        success = s3_service.upload_report(
            file_buffer=pdf_buffer,
            s3_key=metadata.s3_key,
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload report to S3"
            )

        # Generate presigned URL
        download_url = s3_service.generate_presigned_url(metadata.s3_key)

        if not download_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate download URL"
            )

        return ReportResponse(
            report_id=metadata.report_id,
            user_id=metadata.user_id,
            session_id=metadata.session_id,
            generated_at=metadata.generated_at,
            download_url=download_url,
            expires_in=3600,  # 1 hour
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/download/{report_id}")
async def get_download_url(report_id: str, user_id: str):
    """
    Get presigned download URL for a report

    Args:
        report_id: Report identifier
        user_id: User identifier (for authorization)

    Returns:
        Presigned download URL
    """
    try:
        # Construct S3 key
        s3_key = f"reports/{user_id}/{report_id}.pdf"

        # Check if report exists
        if not s3_service.check_report_exists(s3_key):
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )

        # Generate presigned URL
        download_url = s3_service.generate_presigned_url(s3_key)

        if not download_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate download URL"
            )

        return {
            "report_id": report_id,
            "download_url": download_url,
            "expires_in": 3600,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{report_id}")
async def delete_report(report_id: str, user_id: str):
    """
    Delete a report

    Args:
        report_id: Report identifier
        user_id: User identifier (for authorization)

    Returns:
        Success message
    """
    try:
        # Construct S3 key
        s3_key = f"reports/{user_id}/{report_id}.pdf"

        # Delete from S3
        success = s3_service.delete_report(s3_key)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete report"
            )

        return {
            "message": "Report deleted successfully",
            "report_id": report_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "report-service",
    }
