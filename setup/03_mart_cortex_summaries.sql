-- Create our final analytics summary table
CREATE OR REPLACE TABLE DS5111_DB.TXT1SR.MART_CORTEX_SUMMARIES AS
WITH validated_data AS (
    SELECT 
        json_payload:video_id::VARCHAR AS video_id,
        json_payload:cleaned_text::VARCHAR AS transcript_text
    FROM DS5111_DB.TXT1SR.RAW_TRANSCRIPTS
    WHERE LENGTH(json_payload:cleaned_text::VARCHAR) >= 15
)
SELECT 
    video_id,
    -- This calls Snowflake's native 2026 LLM engine instantly
    SNOWFLAKE.CORTEX.SUMMARIZE(transcript_text) AS ai_generated_summary,
    CURRENT_TIMESTAMP() AS processed_at
FROM validated_data;

-- View the final AI results grid!
SELECT * FROM DS5111_DB.TXT1SR.MART_CORTEX_SUMMARIES;
