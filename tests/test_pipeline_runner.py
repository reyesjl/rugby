
import pytest
from unittest.mock import patch, MagicMock
from core.pipeline_runner import PipelineRunner
from core.pipeline_models import VideoProcessingConfig
import subprocess

def minimal_config():
	return {
		'sources': [
			{'type': 'linux_desktop', 'path': '/videos', 'watch_patterns': ['mp4', 'avi']}
		],
		'conversion': {
			'ffmpeg': {
				'video_codec': 'libx264',
				'crf': 23,
				'preset': 'fast',
				'audio_codec': 'aac',
				'audio_bitrate': '128k',
			},
			'parallel_workers': 1
		},
		'indexing': {
			'ai_provider': 'openai',
			'model': 'gpt-4o-mini',
			'batch_size': 10,
			'prompt_model': {}
		}
	}

def test_pipeline_runner_init():
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	assert runner.config == config

@patch('core.pipeline_runner.subprocess.run')
def test_convert_videos_mp4_passthrough(mock_run):
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	video_files = ['/videos/test1.mp4', '/videos/test2.mp4']
	result = runner.convert_videos(video_files)
	assert result == video_files
	mock_run.assert_not_called()

@patch('core.pipeline_runner.subprocess.run')
def test_convert_videos_non_mp4_conversion(mock_run):
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	mock_run.return_value = MagicMock()
	video_files = ['/videos/test1.avi']
	result = runner.convert_videos(video_files)
	assert result == ['/videos/test1_converted.mp4']
	mock_run.assert_called_once()

@patch('core.pipeline_runner.subprocess.run')
def test_convert_videos_ffmpeg_error(mock_run):
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	# Simulate ffmpeg failure with CalledProcessError
	mock_run.side_effect = subprocess.CalledProcessError(
		returncode=1,
		cmd=['ffmpeg'],
		stderr=b'ffmpeg failed'
	)
	video_files = ['/videos/test1.avi']
	# Should not raise, just log error and skip
	result = runner.convert_videos(video_files)
	assert result == []

@patch('core.pipeline_runner.find_video_files')
@patch.object(PipelineRunner, 'convert_videos', return_value=['/videos/test1.mp4'])
def test_run_pipeline(mock_convert, mock_find):
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	mock_find.return_value = ['/videos/test1.mp4']
	runner.run()
	mock_find.assert_called()
	mock_convert.assert_called()

def test_build_index_stub():
	config = VideoProcessingConfig(minimal_config())
	runner = PipelineRunner(config)
	# Should not raise, just pass
	runner.build_index(['/videos/test1.mp4'])
