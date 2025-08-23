# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""
index_manager.py
----------------
This module provides functions for summarizing rugby training session transcripts using OpenAI models.
Vectorizing summaries, storing them in a PostgreSQL database with pgvector, and querying videos by semantic similarity.
"""

import logging
import os

import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from core.pipeline_models import IndexingConfig
from indexing.srt_parser import load_srt_text

# Load environment variables from .env file
load_dotenv()
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASS: str = os.getenv("DB_PASS", "postgres")
DB_NAME: str = os.getenv("DB_NAME", "videos_db")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", 5432))

logger = logging.getLogger(__name__)

# TODO: How will we store an open ai key in production?
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# TODO: Evaluate different model options. This is still decent, but there are faster ones with reduced semantic quality.
vector_model = SentenceTransformer("BAAI/bge-small-en")


def summarize_srt_file(configuration: IndexingConfig, srt_file: str) -> str:
    """
    Summarizes a rugby training session transcript from an SRT file using an OpenAI model.

    Args:
        configuration (IndexingConfig): Configuration object specifying AI provider, model, and prompt details.
        srt_file (str): Path to the SRT file containing the transcript.

    Returns:
        str: A summary of the rugby training session.

    Raises:
        ValueError: If the AI provider is unsupported or the OpenAI API returns no/empty response.
    """
    if configuration.ai_provider != "openai":
        # TODO: More providers?
        raise ValueError(
            f"Unsupported AI provider: {configuration.ai_provider}. Only 'openai' is supported."
        )

    logger.debug(f"Summarizing SRT file: {srt_file}")
    transcript = load_srt_text(srt_file)

    prompt = f"""
    {configuration.prompt_model.instructions}

    Here is the transcript:

    {transcript}
    """
    model = configuration.model
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"{configuration.prompt_model.system}"},
            {"role": "user", "content": prompt},
        ],
        temperature=1
        if model == "gpt-5o"
        else 0.3,  # GPT5 no longer supports temperature besides 1
    )

    if (
        not response.choices
        or len(response.choices) == 0
        or not response.choices[0].message.content
    ):
        raise ValueError("No response from OpenAI API")

    summary = response.choices[0].message.content.strip()
    if not summary:
        raise ValueError("Empty summary returned from OpenAI API")

    logger.debug("Summary generated")
    logger.debug(f"Summary: {summary}")

    return response.choices[0].message.content


def vectorize_and_store_summary(summary: str, video_file_path: str) -> None:
    """
    Vectorizes a summary using a sentence transformer and stores it in the PostgreSQL database.

    Args:
        summary (str): The summary text to vectorize.
        video_file_path (str): The file path of the associated video.
    """
    logger.debug(f"Vectorizing summary for video: {video_file_path}")
    summary_embedding: list = vector_model.encode(summary).tolist()

    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )
    cur = conn.cursor()

    # TODO: How should we handle duplicates? The embedding will be different
    #       and the summary may differ slightly as well
    # Insert record with vector
    cur.execute(
        """
        INSERT INTO videos (summary, path, embedding)
        VALUES (%s, %s, %s)
        """,
        (summary, video_file_path, summary_embedding),
    )

    conn.commit()
    cur.close()
    conn.close()
    logger.debug(f"Vectorized summary for video: {video_file_path}")


def query_videos(query: str, result_limit: int = 5) -> tuple[list[str], list[str]]:
    """
    Queries the database for videos most semantically similar to the input query using vector search.

    Args:
        query (str): The search query string.
        result_limit (int): Maximum number of results to return.

    Returns:
        Tuple[list[str], list[str]]: A tuple containing two lists
            the first with video summaries and the second with their file paths.
    """
    logger.debug(f"Querying videos with query: {query} and limit: {result_limit}")
    query_embedding = vector_model.encode(query).tolist()

    conn = psycopg.connect(
        "dbname=videos_db user=postgres password=postgres host=localhost"
    )
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, summary, path
        FROM videos
        ORDER BY embedding <-> %s::vector
        LIMIT %s;""",
        (query_embedding, result_limit),
    )

    results = cur.fetchall()
    summaries = [result[1] for result in results]
    paths = [result[2] for result in results]

    logger.debug(f"Found {len(paths)} videos matching query: {query}")

    cur.close()
    conn.close()

    return (summaries, paths)


def video_file_indexed(file_path: str) -> bool:
    """
    Checks if a video file has already been indexed in the database.

    Args:
        file_path (str): The file path of the video to check.

    Returns:
        bool: True if the video is indexed, False otherwise.
    """
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )
    cur = conn.cursor()

    cur.execute("SELECT EXISTS(SELECT 1 FROM videos WHERE path = %s)", (file_path,))
    row = cur.fetchone()
    exists = row[0] if row is not None else False
    logger.debug(f"Video file indexed check for {file_path}: {exists}")

    cur.close()
    conn.close()

    return exists
