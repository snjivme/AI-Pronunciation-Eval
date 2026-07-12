from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks
import os
import time

from app.utils import save_uploaded_file, get_audio_duration
from app.gemini import evaluate_pronunciation

from fastapi.responses import FileResponse
from app.pdf_generator import generate_pdf

router = APIRouter()


def cleanup_old_reports(max_age_seconds=86400):
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return
    now = time.time()
    for filename in os.listdir(reports_dir):
        file_path = os.path.join(reports_dir, filename)
        if os.path.isfile(file_path):
            file_creation_time = os.path.getmtime(file_path)
            if (now - file_creation_time) > max_age_seconds:
                try:
                    os.remove(file_path)
                    print(f"Cleaned up old report: {filename}")
                except Exception as e:
                    print(f"Failed to delete old report {filename}: {e}")


@router.get("/health")
def health():
    return {"status": "OK"}


@router.post("/upload-audio")
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    print("Filename:", file.filename)
    print("Content-Type:", file.content_type)

    # Save uploaded file
    file_path = save_uploaded_file(file)

    # Get audio duration
    duration = get_audio_duration(file_path)

    if duration is None:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail="Unable to read audio duration."
        )

    # Assignment requirement
    if duration < 30 or duration > 45:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail="Audio duration must be between 30 and 45 seconds."
        )

    # Gemini evaluation
    evaluation = evaluate_pronunciation(file_path)

    # Check for evaluation errors
    if "error" in evaluation and "language" not in evaluation:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {evaluation['error']}"
        )

    # Reject non-English audio
    detected_lang = evaluation.get("language", "en")
    if detected_lang != "en":
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=evaluation.get("error", "Please upload an English audio file.")
        )

    print("Detected language:", detected_lang)
    print("Transcript:", evaluation.get("transcript", ""))

    pdf_path = generate_pdf(
        filename=file.filename,
        duration=round(duration, 2),
        language=detected_lang,
        transcript=evaluation.get("transcript", ""),
        corrected_transcript=evaluation.get("corrected_transcript", ""),
        evaluation=evaluation
    )

    # Delete uploaded file after processing
    if os.path.exists(file_path):
        os.remove(file_path)

    # Clean up old reports in the background
    background_tasks.add_task(cleanup_old_reports)

    return {
        "message": "Audio evaluated successfully",
        "filename": file.filename,
        "duration": round(duration, 2),
        "language": detected_lang,
        "transcript": evaluation.get("transcript", ""),
        "corrected_transcript": evaluation.get("corrected_transcript", ""),
        "pdf_download_url": (
            f"{request.base_url}download-report/"
            f"{os.path.basename(pdf_path)}"
        ),
        "evaluation": {
            "overall_score": evaluation.get("overall_score", 0),
            "pronunciation_score": evaluation.get("pronunciation_score", 0),
            "fluency_score": evaluation.get("fluency_score", 0),
            "clarity_score": evaluation.get("clarity_score", 0),
            "pace": evaluation.get("pace", "Good"),
            "mispronounced_words": evaluation.get("mispronounced_words", []),
            "strengths": evaluation.get("strengths", []),
            "suggestions": evaluation.get("suggestions", []),
            "overall_feedback": evaluation.get("overall_feedback", "")
        }
    }


@router.get("/download-report/{filename}")
def download_report(filename: str):
    file_path = os.path.join("reports", filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )


@router.delete("/delete-report/{filename}")
def delete_report(filename: str):
    filename = os.path.basename(filename)
    file_path = os.path.join("reports", filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return {"message": "Report deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete report: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )