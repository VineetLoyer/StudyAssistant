import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    jwt_issuer: str = os.getenv("JWT_ISSUER", "cequence")
    jwt_aud: str = os.getenv("JWT_AUDIENCE", "study-mcp")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-demo-secret-change-me")
    fwd_user_header: str = os.getenv("FORWARDED_USER_HEADER", "x-user-id")

settings = Settings()