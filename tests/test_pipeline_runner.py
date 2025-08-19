import pytest
from core.pipeline_runner import PipelineRunner
from core.pipeline_models import VideoProcessingConfig

def _make_config(paths):
    sources = [{"type": "linux_desktop", "path": p, "watch_patterns": ["*.mp4"]} for p in paths]
    return VideoProcessingConfig({"sources": sources, "conversion": {}, "indexing": {}})

def test_pipeline_runner_scans_and_aggregates(monkeypatch, capsys):
    config = _make_config(["/src/A", "/src/B"])
    calls = []
    def fake_find_video_files(path, recursive=True):
        calls.append((path, recursive))
        if path.endswith("A"):
            return ["/src/A/a1.mp4", "/src/A/a2.mp4"]
        if path.endswith("B"):
            return ["/src/B/b1.mp4"]
        return []
    monkeypatch.setattr("core.pipeline_runner.find_video_files", fake_find_video_files)

    PipelineRunner(config).run()
    out = capsys.readouterr().out
    assert "found 2 videos." in out
    assert "found 1 videos." in out
    assert "[OK] Total video files found: 3" in out
    assert calls == [("/src/A", True), ("/src/B", True)]

def test_pipeline_runner_continues_on_error(monkeypatch, capsys):
    config = _make_config(["/src/A", "/src/B"])
    def fake_find_video_files(path, recursive=True):
        if path.endswith("A"):
            raise RuntimeError("boom")
        return ["/src/B/b1.mp4"]
    monkeypatch.setattr("core.pipeline_runner.find_video_files", fake_find_video_files)

    PipelineRunner(config).run()
    out = capsys.readouterr().out
    assert "[ERROR] boom" in out
    assert "[OK] Total video files found: 1" in out