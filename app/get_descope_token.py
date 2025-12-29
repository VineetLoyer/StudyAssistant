import os, getpass
from descope import DescopeClient

PROJECT_ID = "P32CDMRQQQzTtblWVkRrwtO1zOfj"
client = DescopeClient(project_id=PROJECT_ID)

login_id = "vloyer@test.com"
password = "Welcome@123!"

login_id = "vloyer@test.com"
password = "Welcome@123!"

# Sign up or fallback to sign-in if user already exists
try:
    resp = client.password.sign_up(login_id=login_id, password=password)
    print("✅ User signed up:", resp)
except Exception as e:
    print(f"ℹ️  User likely exists; continuing with sign-in. Error: {e}")

try:
    resp = client.password.sign_in(login_id=login_id, password=password)
    
    session_jwt = resp.get("sessionToken", {}).get("jwt")
    refresh_jwt = resp.get("refreshSessionToken", {}).get("jwt")
    
    print("\nSESSION_JWT:\n", session_jwt)
    print("\nREFRESH_JWT:\n", refresh_jwt)
    
    # Optional: Set environment variable for easy access
    if session_jwt:
        os.environ["DESCOPE_SESSION_JWT"] = session_jwt
        print(f"\n✅ Session JWT stored in environment variable")
        
except Exception as e:
    print(f"❌ Sign-in failed: {e}")
