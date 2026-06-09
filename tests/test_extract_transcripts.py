import sys
import io
import json
import pytest
from youtube_transcript_api import YouTubeTranscriptApi

# Import the executable main entry point loop from your pipeline package directory
from bin.extract_transcripts import main

class MockTranscriptContainer:
    """Mimics the 2026 .to_raw_data() array output return schema"""
    def to_raw_data(self):
        return [
            {"start": 10.5, "text": "Automated container tracking loop text entry."}
        ]

def test_extract_transcripts_main_pipeline_stream(monkeypatch, capsys):
    """
    Verifies that the main() entrypoint loop correctly processes video IDs via stdin
    and outputs structured JSON Lines objects via stdout without hitting the internet.
    """
    # 1. Mock the external third-party API fetch dependency
    def stubbed_fetch_route(self, video_id):
        return MockTranscriptContainer()
    monkeypatch.setattr(YouTubeTranscriptApi, "fetch", stubbed_fetch_route)

    # 2. Mock Standard Input (sys.stdin) to feed a fake video ID into your script
    mock_input_stream = io.StringIO("fake_video_999\n")
    monkeypatch.setattr(sys, "stdin", mock_input_stream)

    # 3. Trigger your script's main entry point execution loop directly
    main()

    # 4. Intercept the standard console terminal print buffers using capsys
    captured_output = capsys.readouterr()
    
    # Clean up trailing whitespace and isolate rows
    stdout_lines = captured_output.out.strip().split("\n")

    # 5. Execute structural validations against the emitted JSON Lines payload contract
    assert len(stdout_lines) == 1, "The pipeline loop should emit exactly one row per valid input ID."
    
    parsed_json_line = json.loads(stdout_lines[0])
    
    assert parsed_json_line["video_id"] == "fake_video_999"
    assert "Automated container tracking" in parsed_json_line["raw_text"]
