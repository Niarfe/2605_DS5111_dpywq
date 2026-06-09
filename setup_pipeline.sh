#!/usr/bin/env bash
# ==============================================================================
# DS5111 - 2026 AI-Augmented Pipeline Setup Script
# Run: bash setup_pipeline.sh
# ==============================================================================

echo "🚀 Materializing 5111 Data Pipeline workspace..."

# 1. Create the Directory Hierarchy
mkdir -p pipeline/data/watch_dir
mkdir -p pipeline/data/processing
mkdir -p pipeline/logs
mkdir -p pipeline/scripts

# ==============================================================================
# FILE: pipeline/scripts/clean_ids.py
# ==============================================================================
cat << 'EOF' > pipeline/scripts/clean_ids.py
import sys
import logging

# Configure operational logging to a localized audit file
logging.basicConfig(
    filename='pipeline/logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    seen_ids = set()
    logging.info("Pipeline Step 1 (ID Filter) started.")
    
    # Read row-by-row from standard input (the Linux stream)
    for line in sys.stdin:
        yt_id = line.strip()
        
        # Validation Logic: Skip empty or malformed YouTube IDs
        if not yt_id or len(yt_id) != 11: 
            logging.error(f"Malformed ID rejected: '{yt_id}'")
            continue
            
        # De-duplication Logic
        if yt_id in seen_ids:
            logging.warning(f"Duplicate ID skipped: '{yt_id}'")
            continue
            
        # Deliver clean data down the pipe to stdout
        seen_ids.add(yt_id)
        sys.stdout.write(f"{yt_id}\n")
        sys.stdout.flush()

    logging.info(f"Pipeline Step 1 finished. Forwarded {len(seen_ids)} unique IDs.")

if __name__ == '__main__':
    main()
EOF

# ==============================================================================
# FILE: pipeline/scripts/fetch_transcripts.py
# ==============================================================================
cat << 'EOF' > pipeline/scripts/fetch_transcripts.py
import sys
import os
import json
import logging
from google import genai
from google.genai import types

logging.basicConfig(
    filename='pipeline/logs/pipeline_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    logging.info("Pipeline Step 2 (Gemini Cleaner) started.")
    
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
        
        # Simulated placeholder text (simulate fetching YouTube text before LLM call)
        raw_text = f"[00:05] Context for {video_id}. Read 'Clean Code'. [01:15] Learn PyTorch."
        
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
EOF

# ==============================================================================
# FILE: pipeline/scripts/load_snowflake.py
# ==============================================================================
cat << 'EOF' > pipeline/scripts/load_snowflake.py
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
EOF

# ==============================================================================
# FILE: pipeline/scripts/orchestrator.sh
# ==============================================================================
cat << 'EOF' > pipeline/scripts/orchestrator.sh
#!/usr/bin/env bash
# Resolves race conditions by atomizing inputs before execution

WATCH_DIR="pipeline/data/watch_dir"
PROCESSING_DIR="pipeline/data/processing"

# Check if there are any pending text files dropped via SSH
if [ -n "$(ls -A $WATCH_DIR/*.txt 2>/dev/null)" ]; then
    echo "Found incoming ingestion manifests. Orchestrating..."
    
    # Securely move all text manifests to a processing isolation boundary
    mv $WATCH_DIR/*.txt $PROCESSING_DIR/
    
    # Combine entries, invoke the Unix pipe topology, and pipe cleanly
    cat $PROCESSING_DIR/*.txt | \
        python3 pipeline/scripts/clean_ids.py | \
        python3 pipeline/scripts/fetch_transcripts.py | \
        python3 pipeline/scripts/load_snowflake.py
        
    # Clear artifacts post successful processing run
    rm $PROCESSING_DIR/*.txt
fi
EOF

# ==============================================================================
# FILE: pipeline/crontab_template.txt
# ==============================================================================
cat << 'EOF' > pipeline/crontab_template.txt
# ------------------------------------------------------------------------------
# 5111 Student Lab: Cron Orchestration Engine Template
# Note: Cron environments are sparse. Paths must explicitly be absolute paths.
# ------------------------------------------------------------------------------
# Run every minute to scan the drop folder for new input files
* * * * * /usr/bin/bash /absolute/path/to/pipeline/scripts/orchestrator.sh
EOF

# Ensure shell drivers are instantly runnable
chmod +x pipeline/scripts/orchestrator.sh

echo "✅ Environment generated! Structure available under 'pipeline/'"
echo "   -> Run pipeline manually with: bash pipeline/scripts/orchestrator.sh"
