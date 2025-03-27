from faster_whisper import WhisperModel
import io
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
import torch
from fastapi.responses import JSONResponse
import json
import uvicorn
from typing import Annotated

from fastapi import FastAPI, Form
import asyncio
import os
import time
from contextlib import asynccontextmanager
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

transcribe_model = None
BEAM_SIZE = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    global transcribe_model, BEAM_SIZE
    load_dotenv()
    model_name = os.environ.get("MODEL", "tiny")
    BEAM_SIZE = os.environ.get("BEAM_SIZE", 5)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    transcribe_model = WhisperModel(model_name, device=device, compute_type="float16")
    yield


app = FastAPI(lifespan=lifespan, title="Fully Self-Contained WebSocket Server")

# Run on GPU with FP16


# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")


@app.post("/v1/audio/transcriptions")
async def tokenize_audio(model: Annotated[str, Form()], file: UploadFile = File(...)):
    try:
        # Read file
        file_obj = await file.read()

        segments, info = transcribe_model.transcribe(
            io.BytesIO(file_obj), beam_size=BEAM_SIZE, language="en")
        final = ""
        for segment in segments:
            final += segment.text

        return JSONResponse(content={
            "text": final,
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", port=3348, host = "0.0.0.0")