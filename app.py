import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

load_dotenv()

from extraction import extract_from_pdf, get_demo_data
from validation import validate_all
from fridge_extraction import extract_fridge_from_pdf, get_fridge_demo_data
from fridge_validation import validate_fridge

app = FastAPI(title="ELS Registration Assistant")


def _get_extractor(product_type):
    if product_type == "refrigerator":
        return extract_fridge_from_pdf, get_fridge_demo_data, validate_fridge
    return extract_from_pdf, get_demo_data, validate_all

BASE_DIR = Path(__file__).parent
SUBMISSIONS_DIR = BASE_DIR / "submissions"
SUBMISSIONS_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def _build_response(extracted, results):
    can_submit = results["summary"]["failed"] == 0
    return {
        "status": "ok",
        "can_submit": can_submit,
        "extracted": extracted,
        "validation": results,
    }


@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/supplier")
async def supplier_view():
    return FileResponse(BASE_DIR / "static" / "supplier.html")


@app.get("/officer")
async def officer_view():
    return FileResponse(BASE_DIR / "static" / "officer.html")


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), product_type: str = "tv"):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 20MB)")

    extract_fn, _, validate_fn = _get_extractor(product_type)
    try:
        extracted = extract_fn(pdf_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    results = validate_fn(extracted)
    resp = _build_response(extracted, results)
    resp["product_type"] = product_type
    return JSONResponse(resp)


@app.get("/api/demo")
async def demo(product_type: str = "tv"):
    _, demo_fn, validate_fn = _get_extractor(product_type)
    extracted = demo_fn()
    results = validate_fn(extracted)
    resp = _build_response(extracted, results)
    resp["product_type"] = product_type
    return JSONResponse(resp)


@app.post("/api/submit")
async def submit_registration(request: Request):
    body = await request.json()
    extracted = body.get("extracted")
    validation = body.get("validation")
    edited_fields = body.get("edited_fields", {})
    product_type = body.get("product_type", "tv")
    field_sources = body.get("field_sources", {})

    if not extracted or not validation:
        raise HTTPException(400, "Missing extracted or validation data")

    all_checks_pass = validation["summary"]["failed"] == 0
    has_manual_input = any(v == "manual" for v in field_sources.values())
    auto_approved = all_checks_pass and not has_manual_input

    submission_id = str(uuid.uuid4())[:8]
    submission = {
        "id": submission_id,
        "product_type": product_type,
        "submitted_at": datetime.now().isoformat(),
        "brand": edited_fields.get("brand", ""),
        "model": edited_fields.get("model_numbers", ""),
        "report_ref": edited_fields.get("test_report_reference_no", ""),
        "status": "Approved" if auto_approved else "Pending Review",
        "auto_approved": auto_approved,
        "approved_by": "system" if auto_approved else None,
        "approved_at": datetime.now().isoformat() if auto_approved else None,
        "registration_fields": edited_fields,
        "field_sources": field_sources,
        "original_extracted": extracted.get("registration_fields", {}),
        "extracted": extracted,
        "validation": validation,
    }

    filepath = SUBMISSIONS_DIR / f"{submission_id}.json"
    with open(filepath, "w") as f:
        json.dump(submission, f, indent=2)

    return JSONResponse({
        "status": "ok",
        "submission_id": submission_id,
        "auto_approved": auto_approved,
    })


@app.post("/api/submissions/{submission_id}/resubmit")
async def resubmit(submission_id: str, request: Request):
    filepath = SUBMISSIONS_DIR / f"{submission_id}.json"
    if not filepath.exists():
        raise HTTPException(404, "Submission not found")

    with open(filepath) as f:
        data = json.load(f)

    if data["status"] != "Returned":
        raise HTTPException(400, "Only returned submissions can be re-submitted")

    body = await request.json()
    edited_fields = body.get("edited_fields", {})
    field_sources = body.get("field_sources", {})

    all_pass = data["validation"]["summary"]["failed"] == 0
    has_manual = any(v == "manual" for v in field_sources.values())

    now = datetime.now().isoformat()
    if "history" not in data:
        data["history"] = []
    data["history"].append({"action": "resubmit", "by": "supplier", "at": now, "comments": ""})

    data["status"] = "Pending Review"
    data["registration_fields"] = edited_fields
    data["field_sources"] = field_sources
    data["resubmitted_at"] = now

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return JSONResponse({"status": "ok", "submission_id": submission_id})


@app.get("/api/submissions")
async def list_submissions():
    submissions = []
    for filepath in sorted(SUBMISSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(filepath) as f:
            data = json.load(f)
        submissions.append({
            "id": data["id"],
            "product_type": data.get("product_type", "tv"),
            "submitted_at": data["submitted_at"],
            "brand": data.get("brand", ""),
            "model": data.get("model", ""),
            "report_ref": data.get("report_ref", ""),
            "status": data.get("status", "Pending Review"),
            "auto_approved": data.get("auto_approved", False),
            "passed": data["validation"]["summary"]["passed"],
            "total": data["validation"]["summary"]["total"],
            "return_comments": data.get("return_comments", ""),
            "rejection_reason": data.get("rejection_reason", ""),
            "deregister_reason": data.get("deregister_reason", ""),
        })
    return JSONResponse({"submissions": submissions})


@app.get("/api/submissions/{submission_id}")
async def get_submission(submission_id: str):
    filepath = SUBMISSIONS_DIR / f"{submission_id}.json"
    if not filepath.exists():
        raise HTTPException(404, "Submission not found")
    with open(filepath) as f:
        data = json.load(f)
    return JSONResponse(data)


@app.post("/api/submissions/{submission_id}/action")
async def submission_action(submission_id: str, request: Request):
    filepath = SUBMISSIONS_DIR / f"{submission_id}.json"
    if not filepath.exists():
        raise HTTPException(404, "Submission not found")

    body = await request.json()
    action = body.get("action")
    comments = body.get("comments", "")

    valid_actions = ("approve", "reject", "return", "delete", "deregister")
    if action not in valid_actions:
        raise HTTPException(400, f"Invalid action. Must be one of: {', '.join(valid_actions)}")

    with open(filepath) as f:
        data = json.load(f)

    now = datetime.now().isoformat()

    if action == "delete":
        filepath.unlink()
        return JSONResponse({"status": "ok", "new_status": "Deleted"})

    if action in ("approve", "reject", "return") and data["status"] != "Pending Review":
        raise HTTPException(400, f"Cannot {action} a submission with status '{data['status']}'")

    if action == "deregister" and data["status"] != "Approved":
        raise HTTPException(400, "Only approved submissions can be de-registered")

    if "history" not in data:
        data["history"] = []
    data["history"].append({"action": action, "by": "officer", "at": now, "comments": comments})

    if action == "approve":
        data["status"] = "Approved"
        data["approved_by"] = "officer"
        data["approved_at"] = now
        data["officer_comments"] = comments
    elif action == "reject":
        if not comments.strip():
            raise HTTPException(400, "Rejection reason is required")
        data["status"] = "Rejected"
        data["rejected_by"] = "officer"
        data["rejected_at"] = now
        data["rejection_reason"] = comments
    elif action == "return":
        if not comments.strip():
            raise HTTPException(400, "Return comments are required")
        data["status"] = "Returned"
        data["returned_by"] = "officer"
        data["returned_at"] = now
        data["return_comments"] = comments
    elif action == "deregister":
        if not comments.strip():
            raise HTTPException(400, "De-registration reason is required")
        data["status"] = "De-registered"
        data["deregistered_by"] = "officer"
        data["deregistered_at"] = now
        data["deregister_reason"] = comments

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return JSONResponse({"status": "ok", "new_status": data["status"]})


if __name__ == "__main__":
    import uvicorn

    print("Starting ELS TV Registration Assistant on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
