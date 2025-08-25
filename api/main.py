# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import videos

app = FastAPI()

# Add middleware for vue frontend<->backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # vue frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)


@app.get("/")
def read_root() -> dict:
    return {"msg": "Welcome to the Video Processing API"}
