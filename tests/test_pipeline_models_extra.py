"""Extra coverage for pipeline models: __str__ and to_dict paths."""

from core.pipeline_models import (
    ConversionConfig,
    IndexingConfig,
    PromptModel,
    TranscriptionConfig,
    VideoProcessingConfig,
    VideoSource,
    VideoSourcesConfiguration,
)


def test_prompt_model_to_dict_and_str():
    pm = PromptModel(
        {
            "system": "sys",
            "user": "usr",
            "instructions": "inst",
            "examples": [{"user": "u", "assistant": "a"}],
        }
    )
    d = pm.to_dict()
    assert d["system"] == "sys" and d["user"] == "usr" and d["instructions"] == "inst"
    assert isinstance(d["examples"], list)
    s = str(pm)
    assert "PromptModel(" in s and "system='sys'" in s

    # Empty prompt should omit keys
    empty = PromptModel().to_dict()
    assert empty == {}


def test_video_source_to_dict_and_str_mp4_added_once():
    src = VideoSource(
        {"type": "network_host", "path": "/p", "watch_patterns": ["mp4", "MP4"]}
    )
    # ensure 'mp4' not duplicated unnecessarily
    assert src.watch_patterns.count("mp4") == 1
    d = src.to_dict()
    assert d["type"] == "network_host" and d["path"] == "/p"
    assert "Watch Patterns" in str(src)


def test_video_sources_configuration_str_to_list():
    conf = VideoSourcesConfiguration(
        [
            {"type": "linux_desktop", "path": "/a"},
            {"type": "windows_desktop", "path": "/b", "watch_patterns": ["avi"]},
        ]
    )
    txt = str(conf)
    assert "Source [1]" in txt and "linux_desktop" in txt
    assert isinstance(conf.to_list(), list) and len(conf.to_list()) == 2


def test_conversion_config_str_and_to_dict():
    conv = ConversionConfig(
        {
            "ffmpeg": {
                "video_codec": "libx265",
                "crf": 20,
                "preset": "slow",
                "audio_codec": "mp3",
                "audio_bitrate": "192k",
            },
            "parallel_workers": 2,
        }
    )
    t = str(conv)
    assert "Video Codec" in t and "Parallel Jobs" in t
    d = conv.to_dict()
    assert d["ffmpeg"]["video_codec"] == "libx265" and d["parallel_workers"] == 2


def test_indexing_config_str_to_dict_with_prompt():
    idx = IndexingConfig(
        {
            "ai_provider": "openai",
            "model": "gpt",
            "batch_size": 5,
            "prompt_model": {"system": "s"},
        }
    )
    t = str(idx)
    assert "AI Provider" in t and "Prompt Model" in t
    d = idx.to_dict()
    assert d["prompt_model"]["system"] == "s"


def test_transcription_config_str_to_dict():
    tc = TranscriptionConfig(
        {
            "model_size": "base",
            "language": "es",
            "output_dir": "/out",
            "preserve_tree": False,
            "device": "cpu",
        }
    )
    t = str(tc)
    assert "Model Size" in t and "Preserve" in t
    d = tc.to_dict()
    assert (
        d["language"] == "es"
        and d["preserve_tree"] is False
        and d["output_dir"] == "/out"
    )


def test_video_processing_config_to_dict_and_str():
    cfg = {
        "sources": [
            {"type": "linux_desktop", "path": "/data", "watch_patterns": ["mpg"]}
        ],
        "conversion": {"ffmpeg": {"video_codec": "libx264"}, "parallel_workers": 1},
        "indexing": {"ai_provider": "openai", "model": "gpt-4o-mini", "batch_size": 10},
        "transcription": {
            "model_size": "tiny",
            "language": "en",
            "output_dir": "./transcripts",
            "preserve_tree": True,
        },
    }
    vpc = VideoProcessingConfig(cfg)
    d = vpc.to_dict()
    assert set(d.keys()) == {"sources", "conversion", "indexing", "transcription"}
    s = str(vpc)
    assert s.strip().startswith("{") and "sources" in s
