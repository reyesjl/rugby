"""Cover IndexingConfig __str__ branch with no prompt model values."""

from core.pipeline_models import IndexingConfig


def test_indexing_config_str_no_prompt():
    idx = IndexingConfig(
        {
            "ai_provider": "openai",
            "model": "gpt-4o-mini",
            "batch_size": 10,
            "prompt_model": {},
        }
    )
    s = str(idx)
    assert "Prompt Model  : (none)" in s
