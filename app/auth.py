from typing import List, Optional, Dict, Any
import os
from fastapi import Depends, HTTPException, Header
import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel

from descope import DescopeClient
# from descope.exceptions import DescopeException

from .settings import settings


PROJECT_ID = os.getenv("DESCOPE_PROJECT_ID")
AUD = os.getenv("DESCOPE_AUD", "new-mcp")

_client = DescopeClient(project_id=PROJECT_ID)

def _extract_claims(session_obj: Any) -> Dict[str, Any]:
    """
    Different SDK versions return different shapes (dict with 'claims', or the claims directly).
    Normalize to a dict of claims.
    """
    if not session_obj:
        return {}
    if isinstance(session_obj, dict):
        return session_obj.get("claims") or session_obj
    # Fallback: try attribute access
    return getattr(session_obj, "claims", {}) or {}

def require_user(authorization: Optional[str]) -> Dict[str, Any]:
    """
    Validate a Descope session token.
    Returns the normalized claims dict without enforcing 'aud'.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization")
    
    token = authorization.split(" ", 1)[1].strip()

    try:
        # Validate the session without audience check
        session = _client.validate_session(token)
        claims = _extract_claims(session)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Ensure subject exists
    sub = claims.get("sub") or claims.get("subject")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub'")

    return {"claims": claims, "subject": sub}

class Principal(BaseModel):
    sub: str
    scopes: List[str] = []
    user_id: Optional[str] = None

# Dependency: verify Authorization: Bearer <JWT>
async def get_principal(authorization: str = Header(...), x_user_id: Optional[str] = Header(default=None)) -> Principal:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            audience=settings.jwt_aud,
            options={"require": ["sub", "aud", "iss"]},
        )
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    if claims.get("iss") != settings.jwt_issuer:
        raise HTTPException(status_code=401, detail="Bad issuer")

    scopes = claims.get("scopes") or claims.get("scope") or []
    if isinstance(scopes, str):
        scopes = scopes.split()

    return Principal(sub=claims.get("sub", "anon"), scopes=scopes, user_id=x_user_id)

# Scope guard
class RequireScopes:
    def __init__(self, *needed: str):
        self.needed = set(needed)
    async def __call__(self, principal: Principal = Depends(get_principal)) -> Principal:
        if not self.needed.issubset(set(principal.scopes)):
            missing = self.needed.difference(set(principal.scopes))
            raise HTTPException(status_code=403, detail=f"Missing scopes: {', '.join(sorted(missing))}")
        
