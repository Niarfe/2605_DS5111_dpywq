#!/usr/bin/env python3
import sys
import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(
    filename='logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("Pipeline Step 2B (Gemini Enrichment) started.")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.critical("GEMINI_API_KEY environment variable not set. Exiting.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)

    # Schema definition ensuring structured outputs for native VARIANT insertion
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

    # Consume the staged JSON lines coming from the extraction step via stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            incoming_payload = json.loads(line)
            video_id = incoming_payload.get("video_id")
            raw_text = incoming_payload.get("raw_text")
        except Exception as e:
            logging.error(f"Failed to parse incoming JSON payload row: {str(e)}")
            continue

        logging.info(f"Orchestrating Gemini enrichment for video: {video_id}")
        
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
            # Emit structured JSON strings to stdout for the Snowflake load tool
            sys.stdout.write(f"{response.text}\n")
            sys.stdout.flush()
            
        except Exception as e:
            logging.error(f"Failed processing video {video_id} during LLM generation: {str(e)}")

    logging.info("Pipeline Step 2B finished.")

if __name__ == '__main__':
    main()
