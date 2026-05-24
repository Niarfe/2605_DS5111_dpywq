import sys
import os
import json
import logging
import snowflake.connector

logging.basicConfig(
    filename='pipeline/logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("Pipeline Step 3 (Snowflake Loader) started.")

    # Establish connection using Snowflake Python API pattern
    try:
        ctx = snowflake.connector.connect(
            user=os.getenv('SF_USER'),
            password=os.getenv('SF_PASSWORD'),
            account=os.getenv('SF_ACCOUNT'),
            warehouse=os.getenv('SF_WAREHOUSE'),
            database=os.getenv('SF_DATABASE'),
            schema=os.getenv('SF_SCHEMA')
        )
        cs = ctx.cursor()
    except Exception as e:
        logging.critical(f"Snowflake Connection Failed: {str(e)}")
        sys.exit(1)

    # Ensure our landing table supports VARIANT formats for semi-structured data
    cs.execute("""
        CREATE TABLE IF NOT EXISTS RAW_TRANSCRIPTS (
            json_payload VARIANT,
            inserted_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)

    # Stream JSON elements directly from stdout of the prior script
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            # Validate input is clean stringified JSON before calling database
            json_data = json.loads(line.strip())

            # Safe binding parameter execution to avoid injection flaws
            cs.execute(
                "INSERT INTO RAW_TRANSCRIPTS (json_payload) SELECT PARSE_JSON(%s)",
                (json.dumps(json_data),)
            )
            logging.info(f"Successfully loaded video {json_data.get('video_id')} into Snowflake.")
        except Exception as e:
            logging.error(f"Failed loading JSON line to Snowflake: {str(e)}")

    cs.close()
    ctx.close()
    logging.info("Pipeline Step 3 finished successfully.")

if __name__ == '__main__':
    main()
