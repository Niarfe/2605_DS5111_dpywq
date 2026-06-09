import pytest
from youtube_transcript_api import YouTubeTranscriptApi

# 1. Create a dummy object to mimic the 2026 data serialization payload return structure
class DummyFetchedTranscript:
    def to_raw_data(self):
        return [
            {"start": 0.0, "duration": 2.5, "text": "Hello world"},
            {"start": 2.5, "duration": 3.0, "text": "Data engineering testing"}
        ]

# 2. Construct the isolated pytest execution case using the monkeypatch utility
def test_extract_transcript_method_behavior(monkeypatch):
    
    # Define a stubbed behavior method that bypasses the live web entirely
    def mock_api_fetch_execution(self, video_id):
        assert video_id == "test_id_123"
        return DummyFetchedTranscript()

    # Intercept the 'fetch' attribute on the target API class right before invocation
    monkeypatch.setattr(YouTubeTranscriptApi, "fetch", mock_api_fetch_execution)

    # Instantiate the application interface engine—it now executes your mock natively!
    test_api_client = YouTubeTranscriptApi()
    live_payload = test_api_client.fetch("test_id_123").to_raw_data()

    # Assert that the array serialization layers unpack properly
    assert len(live_payload) == 2
    assert live_payload[1]["text"] == "Data engineering testing"
