#!/usr/bin/env python3
import sys
import os
import json
import logging
import snowflake.connector

# Configure pipeline auditing log
logging.basicConfig(
    filename='pipeline/logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("Pipeline Step 3 (Snowflake Loader) started.")

    # Establish connection using Snowflake Python API pattern
    # Credentials are expected to be loaded in the environment via .env
    try:
        ctx = snowflake.connector.connect(
            user=os.getenv('SF_USER'),
            password=os.getenv('SF_PASSWORD'),
            account=os.getenv('SF_ACCOUNT'),
            warehouse=os.getenv('SF_WAREHOUSE'),
            database=os.getenv('SF_DATABASE'),
            schema=os.getenv('SF_SCHEMA'),
            role=os.getenv("SF_ROLE")
        )
        cs = ctx.cursor()
    except Exception as e:
        logging.critical(f"Snowflake Connection Failed: {str(e)}")
        sys.exit(1)

    try:
        # Ensure our landing table supports VARIANT formats for semi-structured data
        cs.execute("""
            CREATE TABLE IF NOT EXISTS RAW_TRANSCRIPTS (
                json_payload VARIANT,
                inserted_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
    except Exception as e:
        logging.error(f"Failed to verify or create table RAW_TRANSCRIPTS: {str(e)}")
        cs.close()
        ctx.close()
        sys.exit(1)

    # Stream JSON lines directly from stdin (piped from prior script)
    for line in sys.stdin:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        try:
            # Validate input is clean stringified JSON before calling database
            json_data = json.loads(cleaned_line)
            video_id = json_data.get('video_id', 'UNKNOWN_ID')

            # Safe binding parameter execution to avoid SQL injection flaws
            # Select PARSE_JSON(%s) securely converts the stringified JSON to a Snowflake VARIANT
            cs.execute(
                "INSERT INTO RAW_TRANSCRIPTS (json_payload) SELECT PARSE_JSON(%s)",
                (json.dumps(json_data),)
            )
            logging.info(f"Successfully loaded video {video_id} into Snowflake.")
            
        except json.JSONDecodeError as jde:
            logging.error(f"Malformed JSON dropped from stream: {str(jde)} | Line content: {cleaned_line[:100]}")
        except Exception as e:
            logging.error(f"Failed loading JSON line to Snowflake: {str(e)}")

    # Clean up handlers and commit/close connections cleanly
    cs.close()
    ctx.close()
    logging.info("Pipeline Step 3 finished successfully.")

if __name__ == '__main__':
    main()
