import os, time, jwt
secret = os.getenv('JWT_SECRET','dev-demo-secret-change-me')
claims = {
  'iss': os.getenv('JWT_ISSUER','cequence'),
  'aud': os.getenv('JWT_AUDIENCE','study-mcp'),
  'sub': 'vineet', #change as needed
  'scopes': ['materials:read','notes:write','quiz:write','calendar:write'],
  'iat': int(time.time()),
  'exp': int(time.time()) + 3600,
}
print(jwt.encode(claims, secret, algorithm=os.getenv('JWT_ALG','HS256')))
