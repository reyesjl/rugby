# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

from fastapi import APIRouter
from pydantic import BaseModel

from indexing.index_manager import query_videos

router = APIRouter(
    prefix="/videos",  # all routes start with /videos
    tags=["videos"],
)


@router.get("/")
def videos_home() -> dict:
    return {"title": "Welcome to videos Home"}


class VideoModel(BaseModel):
    summary: str
    path: str


@router.get("/search")
def search_videos(query: str, limit: int = 5) -> list[VideoModel]:
    (summaries, paths) = query_videos(query, limit)
    return [VideoModel(summary=s, path=p) for (s, p) in zip(summaries, paths)]
