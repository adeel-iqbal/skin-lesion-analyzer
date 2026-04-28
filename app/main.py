import os
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles
from dotenv import load_dotenv

from app.model import predict, load_model
from app.agent import run_agents
from app.derm_finder import find_dermatologists
from app.pdf_report import generate_pdf

load_dotenv()

BASE = Path(__file__).parent.parent
UPLOAD_DIR = BASE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SkinAI")
app.mount("/static", StaticFiles(directory=str(BASE / "app" / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/reports", StaticFiles(directory=str(BASE / "reports")), name="reports")

templates = Jinja2Templates(directory=str(BASE / "app" / "templates"))


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, load_model)
    print("Model loaded and ready.")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    lat: str = Form(default=""),
    lng: str = Form(default=""),
    language: str = Form(default="en"),
):
    # Save uploaded image
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    image_path = UPLOAD_DIR / filename

    async with aiofiles.open(image_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Run model prediction
    prediction = predict(str(image_path))

    # Run agents and dermatologist search concurrently
    loop = asyncio.get_event_loop()
    agent_task = loop.run_in_executor(None, run_agents, prediction, language)

    lat_f = float(lat) if lat else None
    lng_f = float(lng) if lng else None

    if lat_f and lng_f:
        derm_task = find_dermatologists(lat_f, lng_f)
        agent_output, dermatologists = await asyncio.gather(agent_task, derm_task)
    else:
        agent_output = await agent_task
        dermatologists = []

    # Generate PDF
    pdf_filename = generate_pdf(
        prediction=prediction,
        agent_output=agent_output,
        dermatologists=dermatologists,
        language=language,
        image_path=str(image_path),
    )

    return templates.TemplateResponse("result.html", {
        "request": request,
        "prediction": prediction,
        "agent": agent_output,
        "dermatologists": dermatologists,
        "image_url": f"/uploads/{filename}",
        "pdf_url": f"/reports/{pdf_filename}",
        "language": language,
    })


@app.get("/place-details")
async def place_details(place_id: str):
    import httpx
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        return JSONResponse({"error": "No API key"}, status_code=500)

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,formatted_address",
        "key": key,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        data = resp.json()

    result = data.get("result", {})
    return JSONResponse({
        "phone":   result.get("formatted_phone_number", None),
        "website": result.get("website", None),
        "address": result.get("formatted_address", None),
    })


@app.get("/health")
async def health():
    return {"status": "ok"}
