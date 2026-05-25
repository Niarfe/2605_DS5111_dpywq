import sys
import os
import json
import logging
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

ytt_api = YouTubeTranscriptApi()

logging.basicConfig(
    filename='pipeline/logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("Pipeline Step 2 (Gemini Cleaner) started.")
   
    # Check for core environment configurations
    api_key = os.getenv("GEMINI_API_KEY")
    proxy_user = os.getenv("WEBSHARE_USER")
    proxy_pass = os.getenv("WEBSHARE_PASSWORD")
    
    if not api_key:
        logging.critical("GEMINI_API_KEY environment variable not set. Exiting.")
        sys.exit(1)

    # Instantiate the API client with residential rotating routing
    if proxy_user and proxy_pass:
        logging.info("Proxy credentials detected. Routing traffic via Webshare Residential network.")
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=proxy_user,
                proxy_password=proxy_pass
            )
        )
    else:
        logging.warning("No proxy credentials found. Running with direct raw local IP routing.")
        ytt_api = YouTubeTranscriptApi()

    # Ensure client can authenticate
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.critical("GEMINI_API_KEY environment variable not set. Exiting.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)

    # Schema configuration to enforce valid JSON payloads for Snowflake variant ingestion
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "video_id": {"type": "STRING"},
            "cleaned_text": {"type": "STRING"},
            "tech_terms": {"type": "ARRAY", "items": {"type": "STRING"}},
            "book_names": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["video_id", "cleaned_text"]
    }

    # Stream the cleaned IDs directly from clean_ids.py via stdin
    for line in sys.stdin:
        video_id = line.strip()
        logging.info(f"Processing transcript extraction for video: {video_id}")
        
        try:
            # 2. Call the modern .fetch() instance method
            fetched_transcript = ytt_api.fetch(video_id)
            
            # 3. Use the built-in serializer to grab the raw data array
            transcript_list = fetched_transcript.to_raw_data()
            
            # 4. Stitch the segments into a single raw text string for Gemini
            raw_text = " ".join([f"[{item['start']}] {item['text']}" for item in transcript_list])
            
        except Exception as e:
            logging.error(f"Failed to fetch YouTube transcript for {video_id}: {str(e)}")
            continue

        prompt = f"""
        You are an elite data engineer. Clean this transcript text for video_id '{video_id}'.
        1. Strip all timestamps and duration codes.
        2. Extract technical architecture terms and books.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[prompt, raw_text],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                )
            )
            # Emit raw structured JSON tokens to stdout for next step
            sys.stdout.write(f"{response.text}\n")
            sys.stdout.flush()
            
        except Exception as e:
            logging.error(f"Failed processing video {video_id}: {str(e)}")

    logging.info("Pipeline Step 2 finished.")

if __name__ == '__main__':
    main()
