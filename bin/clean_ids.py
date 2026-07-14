import sys
import logging

# Configure operational logging to a localized audit file
logging.basicConfig(
    filename='logs/pipeline_audit.log',
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
