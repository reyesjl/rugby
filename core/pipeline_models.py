
from enum import Enum
from typing import List


# ------------------------
# Video Processing Models
# ------------------------
class VideoSourceType(Enum):
    """Enumeration of possible video source types."""
    LINUX_DESKTOP   = "linux_desktop"
    WINDOWS_DESKTOP = "windows_desktop"
    NETWORK_HOST    = "network_host"
 


class VideoSource:
    """
    Represents a video source with its configuration.
    Initialized from a configuration dictionary.
    """

    def __init__(self, source_config: dict):
        self.source_type: VideoSourceType = VideoSourceType(source_config.get('type', 'windows_desktop'))
        self.path: str = source_config.get('path', 'TODO')
        self.watch_patterns: List[str] = source_config.get('watch_patterns', [])

    def __str__(self) -> str:
        return (
            f"VideoSource(type={self.source_type.value}, "
            f"path={self.path}, "
            f"watch_patterns={self.watch_patterns})"
        )


class VideoSourcesConfiguration:
    """
    Holds a list of video source configurations.
    Can be initialized from a list of source dictionaries.
    """

    def __init__(self, sources: List[dict] = []):
        self.sources: List[VideoSource] = []
        if len(sources) == 0:
            print("No Video Sources Configuration provided.")
            return

        for source in sources:
            self.sources.append(VideoSource(source))

    def __str__(self) -> str:
        res = ""
        for ix,source in enumerate(self.sources):
            res += f"\n\t\tSource [{ix}]: {source}"
        return res

# ------------------------
# Conversion Models
# ------------------------
class FFmpegConfig:
    """
    Configuration for FFmpeg video and audio encoding settings.
    Initialized from a configuration dictionary.
    """
    def __init__(self, ffmpeg_config: dict = {}):
        self.video_codec: str = ffmpeg_config.get('video_codec', 'libx264')
        self.crf: int = ffmpeg_config.get('crf', 23)
        self.preset: str = ffmpeg_config.get('preset', 'fast')
        self.audio_codec: str = ffmpeg_config.get('audio_codec', 'aac')
        self.audio_bitrate: str = ffmpeg_config.get('audio_bitrate', '128k')

    def __str__(self) -> str:
        return (
            f"FFmpegConfig(video_codec={self.video_codec}, crf={self.crf}, "
            f"preset={self.preset}, audio_codec={self.audio_codec}, "
            f"audio_bitrate={self.audio_bitrate})"
        )

class ConversionConfig:
    """
    Configuration for the video conversion process, including FFmpeg settings and parallelism.
    Initialized from a configuration dictionary.
    """
    def __init__(self, conversion_config: dict = {}):
        ffmpeg_conf = conversion_config.get('ffmpeg', {})
        self.ffmpeg: FFmpegConfig = FFmpegConfig(ffmpeg_conf)
        self.parallel_workers: int = conversion_config.get('parallel_workers', 1)

    def __str__(self) -> str:
        return (
            f"ConversionConfig(ffmpeg={self.ffmpeg}, "
            f"parallel_workers={self.parallel_workers})"
        )

# ------------------------
# Indexing Model
# ------------------------
class IndexingConfig:
    """
    Configuration for the indexing process, including AI provider, model, and batch size.
    Initialized from a configuration dictionary.
    """
    def __init__(self, indexing_config: dict = {}):
        self.ai_provider: str = indexing_config.get('ai_provider', 'openai')
        self.model: str = indexing_config.get('model', 'gpt-4o-mini')
        self.batch_size: int = indexing_config.get('batch_size', 10)

    def __str__(self) -> str:
        return (
            f"IndexingConfig(ai_provider={self.ai_provider}, "
            f"model={self.model}, batch_size={self.batch_size})"
        )

# ------------------------
# Container Model
# ------------------------
class VideoProcessingConfig:
    """
    Container for the entire video processing pipeline configuration, including sources, conversion, and indexing.
    Initialized from a configuration dictionary.
    """
    """Configuration for video processing."""

    def __init__(self, processing_config: dict = {}):
        source_config: List[dict] = processing_config.get('sources', [])
        conversion_config: dict = processing_config.get('conversion', {})
        indexing_config: dict = processing_config.get('indexing', {})

        self.video_sources: VideoSourcesConfiguration = VideoSourcesConfiguration(source_config)
        self.conversion_config: ConversionConfig = ConversionConfig(conversion_config)
        self.indexing_config: IndexingConfig = IndexingConfig(indexing_config)

    def __str__(self) -> str:
        return (
            f"VideoProcessingConfig(\n"
            f"\tSources:{self.video_sources},\n"
            f"\tConversion Configuration: {self.conversion_config},\n"
            f"\tIndexing Configuration:   {self.indexing_config}\n"
            f")"
        )