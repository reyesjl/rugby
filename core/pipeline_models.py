# ------------------------
# Prompt Model
# ------------------------
from typing import List, Optional
import json


def _omit_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


class PromptModel:
    """
    Structured prompt for LLMs, supporting system, user, instructions, and examples.
    """
    def __init__(self, prompt_config: Optional[dict] = None):
        if prompt_config is None:
            prompt_config = {}
        self.system: str = prompt_config.get('system', '').strip()
        self.user: str = prompt_config.get('user', '').strip()
        self.instructions: str = prompt_config.get('instructions', '').strip()
        self.examples: list = prompt_config.get('examples', [])

    def __str__(self) -> str:
        return (
            f"PromptModel(\n  system={repr(self.system)},\n  user={repr(self.user)},\n  instructions={repr(self.instructions)},\n  examples={self.examples}\n)"
        )

    def to_dict(self) -> dict:
        return _omit_empty({
            "system": self.system,
            "user": self.user,
            "instructions": self.instructions,
            "examples": self.examples if self.examples else [],
        })

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
        # Always ensure 'mp4' (case-insensitive) is present, but do not duplicate
        if not any(p.lower() == "mp4" for p in self.watch_patterns):
            self.watch_patterns.append("mp4")

    def __str__(self) -> str:
        watch_patterns = ', '.join(self.watch_patterns) if self.watch_patterns else 'None'
        return (
            f"    Type         : {self.source_type.value}\n"
            f"    Path         : {self.path}\n"
            f"    Watch Patterns: {watch_patterns}"
        )

    def to_dict(self) -> dict:
        return _omit_empty({
            "type": self.source_type.value,
            "path": self.path,
            "watch_patterns": self.watch_patterns if self.watch_patterns else [],
        })


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
        if not self.sources:
            return "  (No video sources configured)"
        res = ""
        for ix, source in enumerate(self.sources):
            res += f"  Source [{ix+1}]:\n{source}\n"
        return res.rstrip()

    def to_list(self) -> List[dict]:
        return [s.to_dict() for s in self.sources]


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
            f"  Video Codec   : {self.video_codec}\n"
            f"  CRF           : {self.crf}\n"
            f"  Preset        : {self.preset}\n"
            f"  Audio Codec   : {self.audio_codec}\n"
            f"  Audio Bitrate : {self.audio_bitrate}"
        )

    def to_dict(self) -> dict:
        return _omit_empty({
            "video_codec": self.video_codec,
            "crf": self.crf,
            "preset": self.preset,
            "audio_codec": self.audio_codec,
            "audio_bitrate": self.audio_bitrate,
        })


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
            f"{self.ffmpeg}\n"
            f"  Parallel Jobs : {self.parallel_workers}"
        )

    def to_dict(self) -> dict:
        return _omit_empty({
            "ffmpeg": self.ffmpeg.to_dict(),
            "parallel_workers": self.parallel_workers,
        })


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
        self.prompt_model: PromptModel = PromptModel(indexing_config.get('prompt_model', {}))

    def __str__(self) -> str:
        res = (
            f"  AI Provider   : {self.ai_provider}\n"
            f"  Model         : {self.model}\n"
            f"  Batch Size    : {self.batch_size}"
        )
        pm = self.prompt_model
        if pm.system or pm.user or pm.instructions or pm.examples:
            res += "\n  Prompt Model:"
            if pm.system:
                res += f"\n    System:      {pm.system.replace(chr(10), chr(10)+'      ')}"
            if pm.user:
                res += f"\n    User:        {pm.user.replace(chr(10), chr(10)+'      ')}"
            if pm.instructions:
                res += f"\n    System:      {pm.system.replace('\\n', '\\n' + '      ')}"
            if pm.user:
                res += f"\n    User:        {pm.user.replace('\\n', '\\n' + '      ')}"
            if pm.instructions:
                res += f"\n    Instructions: {pm.instructions.replace('\\n', '\\n' + '      ')}"
            if pm.examples:
                res += "\n    Examples:"
                for ex in pm.examples:
                    res += f"\n      - user: {ex.get('user', '')}"
                    res += f"\n        assistant: {ex.get('assistant', '')}"
        else:
            res += "\n  Prompt Model  : (none)"
        return res

    def to_dict(self) -> dict:
        return _omit_empty({
            "ai_provider": self.ai_provider,
            "model": self.model,
            "batch_size": self.batch_size,
            "prompt_model": self.prompt_model.to_dict(),
        })


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
        # Compact, machine-readable, omits empty values
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> dict:
        return _omit_empty({
            "sources": self.video_sources.to_list(),
            "conversion": self.conversion_config.to_dict(),
            "indexing": self.indexing_config.to_dict(),
        })