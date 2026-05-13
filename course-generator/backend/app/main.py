from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import courses
from .db.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Course Generator API")

# Setup CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)

import os

# Serve frontend static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: BASE_DIR is .../backend/app. 
# static is at .../backend/static
# frontend is at .../frontend
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "..", "frontend")

# Ensure static directory exists
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
