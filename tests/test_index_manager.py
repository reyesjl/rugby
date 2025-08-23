# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

from unittest.mock import MagicMock, patch

import pytest

from core.pipeline_models import IndexingConfig
from indexing import index_manager


def make_indexing_config(
    ai_provider="openai",
    model="gpt-3.5-turbo",
    instructions="Summarize the transcript.",
    system="You are a helpful assistant.",
):
    return IndexingConfig(
        {
            "ai_provider": ai_provider,
            "model": model,
            "prompt_model": {"instructions": instructions, "system": system},
        }
    )


@patch("indexing.index_manager.openai_client")
@patch("indexing.index_manager.load_srt_text")
def test_summarize_srt_file_success(mock_load_srt, mock_openai):
    config = make_indexing_config()
    mock_load_srt.return_value = "This is a transcript."
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Summary of transcript."
    mock_openai.chat.completions.create.return_value = mock_response
    result = index_manager.summarize_srt_file(config, "dummy.srt")
    assert result == "Summary of transcript."
    mock_load_srt.assert_called_once_with("dummy.srt")
    mock_openai.chat.completions.create.assert_called_once()


@patch("indexing.index_manager.openai_client")
@patch("indexing.index_manager.load_srt_text")
def test_summarize_srt_file_empty_response(mock_load_srt, mock_openai):
    config = make_indexing_config()
    mock_load_srt.return_value = "Transcript."
    mock_response = MagicMock()
    mock_response.choices = []
    mock_openai.chat.completions.create.return_value = mock_response
    with pytest.raises(ValueError, match="No response from OpenAI API"):
        index_manager.summarize_srt_file(config, "dummy.srt")


@patch("indexing.index_manager.openai_client")
@patch("indexing.index_manager.load_srt_text")
def test_summarize_srt_file_empty_summary(mock_load_srt, mock_openai):
    config = make_indexing_config()
    mock_load_srt.return_value = "Transcript."
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "  "
    mock_openai.chat.completions.create.return_value = mock_response
    with pytest.raises(ValueError, match="Empty summary returned from OpenAI API"):
        index_manager.summarize_srt_file(config, "dummy.srt")


def test_summarize_srt_file_unsupported_provider():
    config = make_indexing_config(ai_provider="otherai")
    with pytest.raises(
        ValueError,
        match="Unsupported AI provider: otherai. Only 'openai' is supported.",
    ):
        index_manager.summarize_srt_file(config, "dummy.srt")


# Tests for vectorize_and_store_summary


@patch("indexing.index_manager.vector_model")
@patch("indexing.index_manager.psycopg.connect")
def test_vectorize_and_store_summary_success(mock_connect, mock_vector_model):
    from unittest.mock import MagicMock, patch

    import pytest

    from core.pipeline_models import IndexingConfig
    from indexing import index_manager

    def make_indexing_config(
        ai_provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        instructions: str = "Summarize the transcript.",
        system: str = "You are a helpful assistant.",
    ) -> IndexingConfig:
        return IndexingConfig(
            {
                "ai_provider": ai_provider,
                "model": model,
                "prompt_model": {"instructions": instructions, "system": system},
            }
        )

    @patch("indexing.index_manager.openai_client")
    @patch("indexing.index_manager.load_srt_text")
    def test_summarize_srt_file_success(mock_load_srt, mock_openai):
        config = make_indexing_config()
        mock_load_srt.return_value = "This is a transcript."
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary of transcript."
        mock_openai.chat.completions.create.return_value = mock_response
        result = index_manager.summarize_srt_file(config, "dummy.srt")
        assert result == "Summary of transcript."
        mock_load_srt.assert_called_once_with("dummy.srt")
        mock_openai.chat.completions.create.assert_called_once()

    @patch("indexing.index_manager.openai_client")
    @patch("indexing.index_manager.load_srt_text")
    def test_summarize_srt_file_empty_response(mock_load_srt, mock_openai):
        config = make_indexing_config()
        mock_load_srt.return_value = "Transcript."
        mock_response = MagicMock()
        mock_response.choices = []
        mock_openai.chat.completions.create.return_value = mock_response
        with pytest.raises(ValueError, match="No response from OpenAI API"):
            index_manager.summarize_srt_file(config, "dummy.srt")

    @patch("indexing.index_manager.openai_client")
    @patch("indexing.index_manager.load_srt_text")
    def test_summarize_srt_file_empty_summary(mock_load_srt, mock_openai):
        config = make_indexing_config()
        mock_load_srt.return_value = "Transcript."
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  "
        mock_openai.chat.completions.create.return_value = mock_response
        with pytest.raises(ValueError, match="Empty summary returned from OpenAI API"):
            index_manager.summarize_srt_file(config, "dummy.srt")

    def test_summarize_srt_file_unsupported_provider():
        config = make_indexing_config(ai_provider="otherai")
        with pytest.raises(
            ValueError,
            match="Unsupported AI provider: otherai. Only 'openai' is supported.",
        ):
            index_manager.summarize_srt_file(config, "dummy.srt")

    @patch("indexing.index_manager.vector_model")
    @patch("indexing.index_manager.psycopg.connect")
    def test_vectorize_and_store_summary_success(mock_connect, mock_vector_model):
        summary = "A summary of the video."
        video_path = "/videos/video1.mp4"
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_vector_model.encode.return_value = mock_embedding
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        index_manager.vectorize_and_store_summary(summary, video_path)

        mock_vector_model.encode.assert_called_once_with(summary)
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        actual_sql = mock_cursor.execute.call_args[0][0]
        expected_sql = """
            INSERT INTO videos (summary, path, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (path) DO UPDATE
              SET summary = EXCLUDED.summary,
                  embedding = EXCLUDED.embedding
            """

        def normalize_sql(sql: str) -> str:
            return " ".join(sql.split())

        assert normalize_sql(actual_sql) == normalize_sql(expected_sql)
        assert mock_cursor.execute.call_args[0][1] == (
            summary,
            video_path,
            [0.1, 0.2, 0.3],
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("indexing.index_manager.vector_model")
    @patch("indexing.index_manager.psycopg.connect")
    def test_vectorize_and_store_summary_db_error(mock_connect, mock_vector_model):
        summary = "A summary of the video."
        video_path = "/videos/video1.mp4"
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_vector_model.encode.return_value = mock_embedding
        mock_connect.side_effect = Exception("DB connection failed")

        index_manager.vectorize_and_store_summary(summary, video_path)
        mock_vector_model.encode.assert_called_once_with(summary)
        mock_connect.assert_called_once()

    @patch("indexing.index_manager.psycopg.connect")
    @patch("indexing.index_manager.vector_model")
    def test_query_videos_returns_paths(mock_vector_model, mock_connect):
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_vector_model.encode.return_value = mock_embedding
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "summary1", "/path/to/video1.mp4"),
            (2, "summary2", "/path/to/video2.mp4"),
        ]
        result = index_manager.query_videos("tackle", result_limit=2)
        assert result == ["/path/to/video1.mp4", "/path/to/video2.mp4"]
        mock_vector_model.encode.assert_called_once_with("tackle")
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("indexing.index_manager.psycopg.connect")
    @patch("indexing.index_manager.vector_model")
    def test_query_videos_empty_result(mock_vector_model, mock_connect):
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_vector_model.encode.return_value = mock_embedding
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        result = index_manager.query_videos("try", result_limit=3)
        assert result == []

    @patch("indexing.index_manager.psycopg.connect")
    @patch("indexing.index_manager.vector_model")
    def test_query_videos_result_limit(mock_vector_model, mock_connect):
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_vector_model.encode.return_value = mock_embedding
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "summary1", "/video1.mp4"),
            (2, "summary2", "/video2.mp4"),
            (3, "summary3", "/video3.mp4"),
        ]
        result = index_manager.query_videos("pass", result_limit=2)
        assert result == ["/video1.mp4", "/video2.mp4", "/video3.mp4"]

    @patch("indexing.index_manager.psycopg.connect")
    def test_video_file_indexed_success(mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (True,)
        assert index_manager.video_file_indexed("/path/to/video.mp4") is True

    @patch("indexing.index_manager.psycopg.connect")
    def test_video_file_indexed_no_match(mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (False,)
        assert index_manager.video_file_indexed("/path/to/video.mp4") is False

    @patch("indexing.index_manager.psycopg.connect")
    def test_video_file_indexed_no_match_empty(mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        assert index_manager.video_file_indexed("/path/to/video.mp4") is False
