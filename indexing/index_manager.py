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
from typing import Any, NoReturn

try:  # psycopg may be absent in minimal test env; provide stub so tests can patch
    import psycopg  # type: ignore
except ImportError:  # pragma: no cover - fallback path only for missing dependency
    import types

    def _missing_psycopg(*_args: object, **_kwargs: object) -> NoReturn:  # noqa: D401
        raise ImportError(
            "psycopg not installed; database operations unavailable in test mode"
        )

    psycopg = types.SimpleNamespace(connect=_missing_psycopg)  # type: ignore
try:  # optional dependency (tests may omit python-dotenv)
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover

    def load_dotenv(*_args: object, **_kwargs: object) -> bool:  # type: ignore
        return False


try:  # optional dependency: openai
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover

    class OpenAI:  # type: ignore
        class _Chat:
            class _Completions:
                def create(self, *args: object, **kwargs: object) -> object:  # noqa: D401
                    raise RuntimeError(
                        "OpenAI SDK not installed; this stub should be patched in tests"
                    )

            completions = _Completions()

        chat = _Chat()


try:  # optional dependency: sentence-transformers
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:  # pragma: no cover

    class SentenceTransformer:  # type: ignore
        def __init__(self, *_args: object, **_kwargs: object) -> None:  # noqa: D401
            pass

        def encode(self, _text: str) -> list[float]:  # noqa: D401
            return [0.0]


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
try:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore[arg-type]
except TypeError:  # Stub path: constructor takes no api_key
    openai_client = OpenAI()  # type: ignore[call-arg]
# Load embedding model (fallback stub returns [0.0])
try:  # pragma: no cover - success path
    vector_model = SentenceTransformer("BAAI/bge-small-en")
except Exception:  # pragma: no cover - offline or missing resources

    class _StubVectorModel:
        def encode(self, _text: str) -> list[float]:  # noqa: D401
            return [0.0]

    vector_model = _StubVectorModel()


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
    # Treat response as Any to avoid strict SDK typing dependency
    response: Any = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"{configuration.prompt_model.system}"},
            {"role": "user", "content": prompt},
        ],
        temperature=1
        if model == "gpt-5o"
        else 0.3,  # GPT5 no longer supports temperature besides 1
    )

    if not getattr(response, "choices", None):
        raise ValueError("No response from OpenAI API")

    summary = response.choices[0].message.content.strip()  # type: ignore[index]
    if not summary:
        raise ValueError("Empty summary returned from OpenAI API")

    logger.debug("Summary generated")
    logger.debug(f"Summary: {summary}")

    return summary


def vectorize_and_store_summary(summary: str, video_file_path: str) -> None:
    """
    Vectorizes a summary using a sentence transformer and stores it in the PostgreSQL database.

    Args:
        summary (str): The summary text to vectorize.
        video_file_path (str): The file path of the associated video.
    """
    logger.debug(f"Vectorizing summary for video: {video_file_path}")
    encoded: Any = vector_model.encode(summary)
    if hasattr(encoded, "tolist"):
        try:
            summary_embedding = encoded.tolist()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            summary_embedding = (
                list(encoded) if not isinstance(encoded, list) else encoded
            )
    elif isinstance(encoded, list):
        summary_embedding = encoded
    else:
        try:
            summary_embedding = list(encoded)  # type: ignore[arg-type]
        except TypeError:
            summary_embedding = [float(encoded)]  # type: ignore[arg-type]

    # Lazy helper to tolerate missing DB in test env
    def _safe_connect() -> Any:  # noqa: D401
        try:
            return psycopg.connect(  # type: ignore[attr-defined]
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("DB unavailable; skipping store: %s", e)
            return None

    conn = _safe_connect()
    if conn is None:
        return
    cur = conn.cursor()

    # Idempotent upsert on unique (path). We overwrite summary + embedding so that
    # reprocessing (e.g. model improvements) refreshes the stored representation.
    cur.execute(
        """
        INSERT INTO videos (summary, path, embedding)
        VALUES (%s, %s, %s)
        ON CONFLICT (path) DO UPDATE
          SET summary = EXCLUDED.summary,
              embedding = EXCLUDED.embedding
        """,
        (summary, video_file_path, summary_embedding),
    )

    conn.commit()
    cur.close()
    conn.close()
    logger.debug(f"Vectorized summary for video: {video_file_path}")


def query_videos(query: str, result_limit: int = 5) -> list[str]:
    """
    Queries the database for videos most semantically similar to the input query using vector search.

    Args:
        query (str): The search query string.
        result_limit (int): Maximum number of results to return.

    Returns:
        list[str]: List of video file paths ranked by similarity to the query.
    """
    logger.debug(f"Querying videos with query: {query} and limit: {result_limit}")
    _enc: Any = vector_model.encode(query)
    if hasattr(_enc, "tolist"):
        try:
            query_embedding = _enc.tolist()
        except Exception:  # noqa: BLE001
            query_embedding = list(_enc)
    else:
        query_embedding = list(_enc)

    try:
        conn = psycopg.connect(  # type: ignore[attr-defined]
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("DB unavailable; skipping query: %s", e)
        return []
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
    paths = [result[2] for result in results]

    logger.debug(f"Found {len(paths)} videos matching query: {query}")

    cur.close()
    conn.close()

    return paths


def video_file_indexed(file_path: str) -> bool:
    """
    Checks if a video file has already been indexed in the database.

    Args:
        file_path (str): The file path of the video to check.

    Returns:
        bool: True if the video is indexed, False otherwise.
    """
    try:
        conn = psycopg.connect(  # type: ignore[attr-defined]
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("DB unavailable; treating %s as not indexed: %s", file_path, e)
        return False
    cur = conn.cursor()

    cur.execute("SELECT EXISTS(SELECT 1 FROM videos WHERE path = %s)", (file_path,))
    row = cur.fetchone()
    exists = row[0] if row is not None else False
    logger.debug(f"Video file indexed check for {file_path}: {exists}")

    cur.close()
    conn.close()

    return exists
