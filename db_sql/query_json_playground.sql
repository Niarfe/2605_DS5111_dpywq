SELECT 
    raw_data:video_id::STRING       AS video_id,
    raw_data:metrics.views::INT     AS view_count,
    raw_data:tags[0]::STRING        AS primary_tag
FROM json_playground;
