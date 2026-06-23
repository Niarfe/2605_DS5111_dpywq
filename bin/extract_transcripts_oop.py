#!/usr/bin/env python3
import sys
import json
import argparse
import os
from abc import ABC, abstractmethod

# =====================================================================
# 1. THE EXTRACTION CONTRACT (Interface)
# =====================================================================
class TranscriptExtractor(ABC):
    @abstractmethod
    def fetch_raw_string(self, source_id: str) -> str:
        """Must accept an identifier string and return raw, unstructured text data."""
        pass


# =====================================================================
# 2. STRATEGY A: THE PRODUCTION YOUTUBE SCRAPER (Version-Agnostic)
# =====================================================================
class YouTubeExtractor(TranscriptExtractor):
    def __init__(self, proxy_url: str = None):
        self.proxy_url = proxy_url

    def fetch_raw_string(self, source_id: str) -> str:
        from youtube_transcript_api import YouTubeTranscriptApi

        original_http = os.environ.get("HTTP_PROXY")
        original_https = os.environ.get("HTTPS_PROXY")
        
        if self.proxy_url:
            os.environ["HTTP_PROXY"] = self.proxy_url
            os.environ["HTTPS_PROXY"] = self.proxy_url

        try:
            if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                proxies_dict = {"http": self.proxy_url, "https": self.proxy_url} if self.proxy_url else None
                transcript_list = YouTubeTranscriptApi.get_transcript(source_id, proxies=proxies_dict)
            else:
                client = YouTubeTranscriptApi()
                if hasattr(client, 'fetch'):
                    transcript_list = client.fetch(source_id).to_raw_data()
                else:
                    transcript_list = client.get_transcript(source_id)

            cleaned_text = " ".join([entry["text"] for entry in transcript_list])
            return cleaned_text
            
        except Exception as e:
            raise RuntimeError(f"YouTube transcript extraction failed for {source_id}: {str(e)}")
        finally:
            if self.proxy_url:
                if original_http: os.environ["HTTP_PROXY"] = original_http
                else: os.environ.pop("HTTP_PROXY", None)
                if original_https: os.environ["HTTPS_PROXY"] = original_https
                else: os.environ.pop("HTTPS_PROXY", None)


# =====================================================================
# 3. STRATEGY B: THE LIVE HTTP CLOUD ARCHIVE (Podcast RSS)
# =====================================================================
class PodcastRssExtractor(TranscriptExtractor):
    def __init__(self, feed_url: str):
        self.feed_url = feed_url

    def fetch_raw_string(self, source_id: str) -> str:
        import requests
        import xml.etree.ElementTree as ET

        try:
            response = requests.get(self.feed_url, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"HTTP Error {response.status_code} accessing RSS feed.")
        except Exception as e:
            raise RuntimeError(f"Network transport failure connecting to feed: {str(e)}")

        try:
            root = ET.fromstring(response.content)
        except Exception as e:
            raise ValueError(f"Failed to compile valid XML tree payload: {str(e)}")

        for item in root.findall('.//item'):
            title_elem = item.find('title')
            desc_elem = item.find('description')
            
            if title_elem is not None and desc_elem is not None:
                title_text = title_elem.text
                if source_id.lower() in title_text.lower():
                    return f"[LIVE PODCAST SHOW NOTES - {title_text}]: {desc_elem.text}"

        raise ValueError(f"No podcast episode matching keyword '{source_id}' located in RSS catalog.")


# =====================================================================
# 4. THE INVARIANT PIPELINE CONTEXT (The Streaming Engine)
# =====================================================================
class ExtractionEngine:
    def __init__(self, strategy: TranscriptExtractor):
        self.strategy = strategy

    def run_stream(self):
        for line in sys.stdin:
            source_id = line.strip()
            if not source_id:
                continue

            try:
                raw_text = self.strategy.fetch_raw_string(source_id)
                
                # FIXED: Kept identical legacy key schema names to protect older tests
                payload = {
                    "video_id": source_id,
                    "raw_text": raw_text
                }
                sys.stdout.write(json.dumps(payload) + "\n")
                sys.stdout.flush()
                
            except Exception as e:
                sys.stderr.write(f"ERROR processing token [{source_id}]: {str(e)}\n")
                sys.stderr.flush()


# =====================================================================
# 5. RUNTIME ENTRYPOINT
# =====================================================================
# FIXED: Accept optional argv parameter for native test-framework compatibility
def main(argv=None):
    parser = argparse.ArgumentParser(description="Multi-Source Transcript Ingestion Node.")
    parser.add_argument(
        "--source", 
        choices=["youtube", "podcast"], 
        default="youtube",
        help="Target infrastructure ingestion path strategy (Defaults to youtube)."
    )
    parser.add_argument("--proxy", default=None, help="Optional proxy endpoint URL string.")
    
    # FIXED: Pass the argv variable into parse_args directly
    args = parser.parse_args(argv)

    if args.source == "youtube":
        selected_strategy = YouTubeExtractor(proxy_url=args.proxy)
    elif args.source == "podcast":
        selected_strategy = PodcastRssExtractor(feed_url="https://talkpython.fm/episodes/rss")

    engine = ExtractionEngine(selected_strategy)
    engine.run_stream()

if __name__ == "__main__":
    main()
