-- Master Pipeline Orchestrator
EXECUTE IMMEDIATE FROM @student_pipeline_repo/branches/LAB09_gitops_snowflake/transform/01_stg_youtube_transcripts.sql;
EXECUTE IMMEDIATE FROM @student_pipeline_repo/branches/LAB09_gitops_snowflake/transform/02_dim_videos.sql;
EXECUTE IMMEDIATE FROM @student_pipeline_repo/branches/LAB09_gitops_snowflake/transform/03_fct_entities.sql;
