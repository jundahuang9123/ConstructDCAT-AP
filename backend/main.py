import os
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys

app = FastAPI(title="DCAT-AP Builder API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RUN_SCRIPT = BASE_DIR / "run.sh"
OUTPUT_DIR = BASE_DIR
TTL_FILE = OUTPUT_DIR / "out.ttl"
REPORT_FILE = OUTPUT_DIR / "shacl-report.txt"

@app.get("/")
def read_root():
    return {"message": "DCAT-AP Builder API is running"}

@app.post("/convert")
async def convert_dcat(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")

    input_path = BASE_DIR / "input.xlsx"
    
    # Save the uploaded file
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Execute the run.sh script
    # We pass the input file name. run.sh expects it in the current directory if just filename, 
    # or potentially a path. run.sh does: XLSX="${1:-dcat-v3-example.xlsx}" ... xlsx = '/data/${XLSX}'
    # The docker mount is -v "$PWD":/data. 
    # So we need to run this from BASE_DIR.
    
    cmd = [str(RUN_SCRIPT), input_path.name]
    
    try:
        # Run synchronous for simplicity in this MVP
        result = subprocess.run(
            cmd, 
            cwd=BASE_DIR, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Validation or Generation failed",
                    "details": result.stderr + "\n" + result.stdout,
                    "report": _read_report_safe()
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Conversion successful",
            "report": _read_report_safe(),
            "download_url": "/download/ttl"
        }
    )

@app.get("/download/ttl")
def download_ttl():
    if not TTL_FILE.exists():
        raise HTTPException(status_code=404, detail="TTL file not found. Run conversion first.")
    return FileResponse(TTL_FILE, media_type="text/turtle", filename="dcat-ap.ttl")

def _read_report_safe():
    if REPORT_FILE.exists():
        return REPORT_FILE.read_text(encoding="utf-8")
    return "No report generated."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
