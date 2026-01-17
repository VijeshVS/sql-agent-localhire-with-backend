from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

clients: List[asyncio.Queue] = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


AGENTS_DIR = os.path.abspath("./agents")

SQL_BASE_DIR = os.path.join(AGENTS_DIR, "notify_agent")
SQL_INPUT_FILE = os.path.join(SQL_BASE_DIR, "input.json")
SQL_OUTPUT_FILE = os.path.join(SQL_BASE_DIR, "output.txt")

class CompleteRequest(BaseModel):
    input: str
    lat: str
    long: str

@app.post("/complete")
def complete(req: CompleteRequest):
    try:
        with open(SQL_INPUT_FILE, "w") as f:
            json.dump({
                "input": req.input,
                "lat": req.lat,
                "long": req.long
            }, f)
    except Exception as e:
        raise HTTPException(500, f"Failed to write input.json: {e}")

    try:
        print(f"🚀 Running SQL agent with prompt: {req.input}")
        subprocess.run(
            ["crewai", "run"],
            cwd=SQL_BASE_DIR,
            check=True,
            text=True,
            timeout=300
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"CrewAI failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "CrewAI execution timed out")

    if not os.path.exists(SQL_OUTPUT_FILE):
        raise HTTPException(500, "output.txt not found")

    with open(SQL_OUTPUT_FILE, "r") as f:
        return {"result": f.read()}