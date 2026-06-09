-- Dynamic Data Validation Stage
SELECT 
    -- FIX: Added colon syntax to extract from the JSON payload properly
    json_payload:video_id::VARCHAR AS video_id,
    CASE 
        WHEN LENGTH(json_payload:cleaned_text::VARCHAR) < 15 THEN 'FAIL: Content Too Short'
        WHEN json_payload:video_id IS NULL THEN 'FAIL: Missing ID'
        ELSE 'PASS'
    END AS data_quality_status,
    json_payload:cleaned_text::VARCHAR AS transcript_text
FROM DS5111_DB.TXT1SR.RAW_TRANSCRIPTS;
