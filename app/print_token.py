import jwt
import json

# Paste your SESSION_JWT here
jwt_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNLMzJDRE1iY2FWMHZxZ1lsWFFHWkQwU3ZPNmR4IiwidHlwIjoiSldUIn0.eyJhbXIiOlsicHdkIl0sImRybiI6IkRTIiwiZW1haWwiOiJ2bG95ZXJAdGVzdC5jb20iLCJleHAiOjE3NTY5MjQ4MTEsImlhdCI6MTc1NjkyMzAxMSwiaXNzIjoiUDMyQ0RNUlFRUXpUdGJsV1ZrUnJ3dE8xek9maiIsInJleHAiOiIyMDI1LTEwLTAxVDE4OjEwOjExWiIsInN1YiI6IlUzMkNTTUJFSnlRVENOVEZ0eDl3emY4dXJrZ1QifQ.auJcGkq_SlkWh8uIWt--7jv-p4PK6-8gqg-yrr37O7dEwep-py9El6MdiV6YMzcEKDCrEj0CzujsqfPar7ITrorYEptAKPn5lB5NQv6QaDFsFsOePY_b-ezNmk8Za-Nf1A6WEWyqvwdjNowur7gr7y-HbA2c8cPQQo9VrIYsitMVilpyMr90GLU1-M6kUJrWfm9cAhph3vDRFmtvhXx237h91TZae4NgU31o6suZcUe6RXmQnmUa4mWv8wV75kEBSNNOi8uoNA1wCtfuuKndnQVD2zLooR2uNG0TCWcLzBOwdXUhrb17_CEZ-4BiUaz3qwfQ2kbPqbHh3-l8_YajuA"

# Decode without verification to see contents
try:
    decoded = jwt.decode(jwt_token, options={"verify_signature": False})
    print("JWT Contents:")
    print(json.dumps(decoded, indent=2))
    
    # Check if audience field exists
    if 'aud' in decoded:
        print(f"\n✅ Audience found: {decoded['aud']}")
    else:
        print("\n❌ No audience field in JWT")
        
except Exception as e:
    print(f"Error decoding JWT: {e}")