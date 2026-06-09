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
