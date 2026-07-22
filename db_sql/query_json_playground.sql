-- Force the Git runner session to locate your data assets
USE DATABASE DS5111_DB;
USE SCHEMA TXT1SR;
USE ROLE DS5111_STUDENT_ROLE;

SELECT 
    raw_data:video_id::STRING       AS video_id,
    raw_data:metrics.views::INT     AS view_count,
    raw_data:tags[0]::STRING        AS primary_tag
FROM json_playground;
