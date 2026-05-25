import csv


# Your raw student roster data
student_data = """name,uvaid,email
albert einstein,abcde,abcde@virginia.edu
paul dirac,aw9vv,aw9vv@virginia.edu
werver heisenberg,8ad0a,8ad0a@virginia.edu"""
student_data = open('student_roster.csv', 'r').read()

def main():
    reader = csv.DictReader(student_data.strip().split('\n'))
    
    print("-- ==============================================================================")
    print("-- DS5111 AUTOMATED STUDENT BATCH PROVISIONING SCRIPT")
    print("-- ==============================================================================\n")
    
    for row in reader:
        username = row['uvaid'].upper()
        # Create a secure temporary password based on their ID
        temp_password = f"DS5111_{username}_2026!"
        
        print(f"-- Provisioning Workspace for: {row['name']} ({row['email']})")
        
        # 1. Create the User (Forcing a password change on first login)
        print(f"CREATE USER IF NOT EXISTS {username} ")
        print(f"    PASSWORD = '{temp_password}' ")
        print(f"    LOGIN_NAME = '{username}' ")
        print(f"    DISPLAY_NAME = '{row['name'].title()}' ")
        print(f"    EMAIL = '{row['email']}' ")
        print(f"    MUST_CHANGE_PASSWORD = TRUE;")
        
        # 2. Assign them to the shared student execution role
        print(f"GRANT ROLE ds5111_student_role TO USER {username};")
 
        # 3. Create their isolated Multi-Level Schema sandbox
        print(f"CREATE SCHEMA IF NOT EXISTS ds5111_db.{username};")
        
        # 4. Hand total ownership of that schema namespace directly to their execution role
        print(f"GRANT OWNERSHIP ON SCHEMA ds5111_db.{username} TO ROLE ds5111_student_role REVOKE CURRENT GRANTS;")
        print("-" * 80 + "\n")     


if __name__ == "__main__":
    main()
