# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

import tempfile

import yaml

from core.pipeline_models import (
    ConversionConfig,
    FFmpegConfig,
    IndexingConfig,
    VideoProcessingConfig,
    VideoSource,
    VideoSourcesConfiguration,
    VideoSourceType,
)


def test_prompt_model_in_indexing_config():
    prompt_model_dict = {
        "system": "You are a video editor AI.",
        "user": "{user_request}",
        "instructions": "Use the available clips.",
        "examples": [
            {"user": "Create a highlight reel.", "assistant": "{...}"},
            {"user": "Show all tries.", "assistant": "{...}"},
        ],
    }
    indexing_dict = {
        "ai_provider": "openai",
        "model": "gpt-4o-mini",
        "batch_size": 10,
        "prompt_model": prompt_model_dict,
    }
    config = IndexingConfig(indexing_dict)
    pm = config.prompt_model
    assert pm.system == "You are a video editor AI."
    assert pm.user == "{user_request}"
    assert pm.instructions == "Use the available clips."
    assert isinstance(pm.examples, list)
    assert pm.examples[0]["user"] == "Create a highlight reel."
    assert pm.examples[1]["assistant"] == "{...}"


def test_prompt_model_in_video_processing_config():
    prompt_model_dict = {
        "system": "System message.",
        "user": "User message.",
        "instructions": "Instructions here.",
        "examples": [{"user": "Prompt1", "assistant": "Resp1"}],
    }
    config_dict = {
        "sources": [],
        "conversion": {},
        "indexing": {
            "ai_provider": "openai",
            "model": "gpt-4o-mini",
            "batch_size": 10,
            "prompt_model": prompt_model_dict,
        },
    }
    vpc = VideoProcessingConfig(config_dict)
    pm = vpc.indexing_config.prompt_model
    assert pm.system == "System message."
    assert pm.user == "User message."
    assert pm.instructions == "Instructions here."
    assert isinstance(pm.examples, list)
    assert pm.examples[0]["assistant"] == "Resp1"


def test_video_source_type_enum_values():
    assert VideoSourceType.LINUX_DESKTOP.value == "linux_desktop"
    assert VideoSourceType.WINDOWS_DESKTOP.value == "windows_desktop"
    assert VideoSourceType.NETWORK_HOST.value == "network_host"


def test_video_source_init_and_str():
    config = {"type": "linux_desktop", "path": "/tmp/data", "watch_patterns": ["mp4"]}
    src = VideoSource(config)
    assert src.source_type == VideoSourceType.LINUX_DESKTOP
    assert src.path == "/tmp/data"
    assert src.watch_patterns == ["mp4"]
    assert "linux_desktop" in str(src)


def test_video_sources_configuration_empty():
    config = VideoSourcesConfiguration([])
    assert isinstance(config.sources, list)
    assert len(config.sources) == 0


def test_video_sources_configuration_multiple():
    configs = [
        {"type": "linux_desktop", "path": "/a"},
        {"type": "windows_desktop", "path": "/b"},
    ]
    vsc = VideoSourcesConfiguration(configs)
    assert len(vsc.sources) == 2
    assert vsc.sources[0].source_type == VideoSourceType.LINUX_DESKTOP
    assert vsc.sources[1].source_type == VideoSourceType.WINDOWS_DESKTOP


def test_ffmpeg_config_defaults():
    ffmpeg = FFmpegConfig({})
    assert ffmpeg.video_codec == "libx264"
    assert ffmpeg.crf == 23
    assert ffmpeg.preset == "fast"
    assert ffmpeg.audio_codec == "aac"
    assert ffmpeg.audio_bitrate == "128k"


def test_conversion_config_defaults():
    conv = ConversionConfig({})
    assert isinstance(conv.ffmpeg, FFmpegConfig)
    assert conv.parallel_workers == 1


def test_indexing_config_defaults():
    idx = IndexingConfig({})
    assert idx.ai_provider == "openai"
    assert idx.model == "gpt-4o-mini"
    assert idx.batch_size == 10


def test_video_processing_config_defaults():
    vpc = VideoProcessingConfig({})
    assert isinstance(vpc.video_sources, VideoSourcesConfiguration)
    assert isinstance(vpc.conversion_config, ConversionConfig)
    assert isinstance(vpc.indexing_config, IndexingConfig)


def test_video_sources_configuration():
    sources = [
        {
            "type": "linux_desktop",
            "path": "/tmp/input1",
            "watch_patterns": ["MPG", "mpg"],
        },
        {
            "type": "network_host",
            "path": "/tmp/input2",
            "watch_patterns": ["MP4", "mp4"],
        },
        {
            "type": "windows_desktop",
            "path": "/tmp/input3",
            "watch_patterns": ["MPG", "mpg"],
        },
    ]
    config = VideoSourcesConfiguration(sources)
    assert isinstance(config.sources, list)
    assert len(config.sources) == 3
    assert config.sources[0].source_type == VideoSourceType.LINUX_DESKTOP
    assert config.sources[0].path == "/tmp/input1"
    assert config.sources[0].watch_patterns == ["MPG", "mpg", "mp4"]
    assert config.sources[1].source_type == VideoSourceType.NETWORK_HOST
    assert config.sources[1].path == "/tmp/input2"
    assert config.sources[1].watch_patterns == ["MP4", "mp4"]
    assert config.sources[2].source_type == VideoSourceType.WINDOWS_DESKTOP
    assert config.sources[2].path == "/tmp/input3"
    assert config.sources[2].watch_patterns == ["MPG", "mpg", "mp4"]


def test_ffmpeg_config_parsing():
    ffmpeg_dict = {
        "video_codec": "libx265",
        "crf": 20,
        "preset": "slow",
        "audio_codec": "mp3",
        "audio_bitrate": "192k",
    }
    ffmpeg_config = FFmpegConfig(ffmpeg_dict)
    assert ffmpeg_config.video_codec == "libx265"
    assert ffmpeg_config.crf == 20
    assert ffmpeg_config.preset == "slow"
    assert ffmpeg_config.audio_codec == "mp3"
    assert ffmpeg_config.audio_bitrate == "192k"


def test_conversion_config_parsing():
    conversion_dict = {
        "ffmpeg": {
            "video_codec": "libx264",
            "crf": 23,
            "preset": "fast",
            "audio_codec": "aac",
            "audio_bitrate": "128k",
        },
        "parallel_workers": 4,
    }
    conversion_config = ConversionConfig(conversion_dict)
    assert isinstance(conversion_config.ffmpeg, FFmpegConfig)
    assert conversion_config.ffmpeg.video_codec == "libx264"
    assert conversion_config.ffmpeg.crf == 23
    assert conversion_config.ffmpeg.preset == "fast"
    assert conversion_config.ffmpeg.audio_codec == "aac"
    assert conversion_config.ffmpeg.audio_bitrate == "128k"
    assert conversion_config.parallel_workers == 4


def test_indexing_config_parsing():
    indexing_dict = {"ai_provider": "openai", "model": "gpt-4o-mini", "batch_size": 10}
    config = IndexingConfig(indexing_dict)
    assert config.ai_provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.batch_size == 10

    # Test defaults
    default_config = IndexingConfig({})
    assert default_config.ai_provider == "openai"
    assert default_config.model == "gpt-4o-mini"


def test_video_processing_config_from_yaml():
    with tempfile.TemporaryDirectory() as tmp_path:
        # Create a sample YAML config file
        config_dict = {
            "sources": [
                {
                    "type": "linux_desktop",
                    "path": str(tmp_path + "/input1"),
                    "watch_patterns": ["MPG", "mpg"],
                },
                {
                    "type": "network_host",
                    "path": str(tmp_path + "/input2"),
                    "watch_patterns": ["MP4", "mp4"],
                },
                {
                    "type": "windows_desktop",
                    "path": str(tmp_path + "/input3"),
                    "watch_patterns": ["MPG", "mpg"],
                },
            ],
            "conversion": {
                "ffmpeg": {
                    "video_codec": "libx264",
                    "crf": 23,
                    "preset": "fast",
                    "audio_codec": "aac",
                    "audio_bitrate": "128k",
                },
                "parallel_workers": 4,
            },
            "indexing": {
                "ai_provider": "openai",
                "model": "gpt-4o-mini",
                "batch_size": 10,
            },
        }
        yaml_path = tmp_path + "/pipeline_test.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(config_dict, f)

        # Load the YAML file as would be done in production
        with open(yaml_path) as f:
            loaded = yaml.safe_load(f)

        # Pass the loaded dict to VideoProcessingConfig
        vpc = VideoProcessingConfig(loaded)

    # Test sources
    assert isinstance(vpc.video_sources, VideoSourcesConfiguration)
    assert len(vpc.video_sources.sources) == 3
    assert vpc.video_sources.sources[0].source_type == VideoSourceType.LINUX_DESKTOP
    assert vpc.video_sources.sources[0].path == str(tmp_path + "/input1")
    assert vpc.video_sources.sources[0].watch_patterns == ["MPG", "mpg", "mp4"]
    assert vpc.video_sources.sources[1].source_type == VideoSourceType.NETWORK_HOST
    assert vpc.video_sources.sources[1].path == str(tmp_path + "/input2")
    assert vpc.video_sources.sources[1].watch_patterns == ["MP4", "mp4"]
    assert vpc.video_sources.sources[2].source_type == VideoSourceType.WINDOWS_DESKTOP
    assert vpc.video_sources.sources[2].path == str(tmp_path + "/input3")
    assert vpc.video_sources.sources[2].watch_patterns == ["MPG", "mpg", "mp4"]

    # Test conversion
    assert isinstance(vpc.conversion_config, ConversionConfig)
    assert vpc.conversion_config.ffmpeg.video_codec == "libx264"
    assert vpc.conversion_config.ffmpeg.crf == 23
    assert vpc.conversion_config.ffmpeg.preset == "fast"
    assert vpc.conversion_config.ffmpeg.audio_codec == "aac"
    assert vpc.conversion_config.ffmpeg.audio_bitrate == "128k"
    assert vpc.conversion_config.parallel_workers == 4

    # Test indexing
    assert isinstance(vpc.indexing_config, IndexingConfig)
    assert vpc.indexing_config.ai_provider == "openai"
    assert vpc.indexing_config.model == "gpt-4o-mini"
    assert vpc.indexing_config.batch_size == 10
