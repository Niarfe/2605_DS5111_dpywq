-- Pile 1: One-Time Global Infrastructure (Executed by YOU as ACCOUNTADMIN)
-- This is your foundation. You run this exactly once at the beginning of the
-- semester to set up for a new group.

-- Run once in an ACCOUNTADMIN Workspace
CREATE DATABASE IF NOT EXISTS ds5111_db;
CREATE WAREHOUSE IF NOT EXISTS ds5111_wh WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;

-- Create the single, shared security permission group for the class
CREATE ROLE IF NOT EXISTS ds5111_student_role;
GRANT USAGE ON DATABASE ds5111_db TO ROLE ds5111_student_role;
GRANT USAGE ON WAREHOUSE ds5111_wh TO ROLE ds5111_student_role;

-- CRITICAL BRIDGE: Allow your own admin user account to use this role for testing
SET active_admin_user = (SELECT CURRENT_USER());
GRANT ROLE ds5111_student_role TO USER IDENTIFIER($active_admin_user);



-- Pile 2: Automated Student Provisioning (Generated via Python, Run by YOU as ACCOUNTADMIN)
-- This is your batch script. It parses your class roster CSV and generates the exact SQL
-- rows needed to give each student an account and an isolated playground.

-- 1. Create the unique user account
CREATE USER IF NOT EXISTS ABCDE
    PASSWORD = 'Ds5111_ABCDE_2026!'
    LOGIN_NAME = 'ABCDE'
    DISPLAY_NAME = 'Albert Einstein'
    EMAIL = 'abcde@virginia.edu'
    MUST_CHANGE_PASSWORD = TRUE;

-- 2. Give them the shared class role
GRANT ROLE ds5111_student_role TO USER ABCDE;

-- 3. Create their isolated sandbox namespace
CREATE SCHEMA IF NOT EXISTS ds5111_db.ABCDE;

-- 4. Sever the admin umbilical cord: Hand total, exclusive ownership of this sandbox to the student role
GRANT OWNERSHIP ON SCHEMA ds5111_db.ABCDE TO ROLE ds5111_student_role REVOKE CURRENT GRANTS;

-- To test a different student account right now:
-- If you want to simulate a completely different student (like Albert Einstein, user ABCDE) right now
-- from your AWS terminal, you do not need to change your master AWS credentials or swap passwords.
-- You just change the destination target in your environment:

-- # 1. Point the pipe destination to Albert's schema
-- export SF_SCHEMA="ABCDE"

-- # 2. Fire the pipe
-- make test_to_sf


