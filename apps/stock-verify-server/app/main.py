from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.core.database import get_db

import os

app = FastAPI(title="Stock Verify Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Router
app.include_router(endpoints.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # Initialize DB if needed, or just log
    # await init_db()
    pass

@app.get("/")
async def read_root():
    return {"status": "Stock Verify Server Running", "docs": "/docs"}
