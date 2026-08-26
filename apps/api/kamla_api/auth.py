from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from kamla_api.config import Settings, get_settings
from kamla_api.db.models import User
from kamla_api.db.session import get_db, set_current_user

bearer_scheme = HTTPBearer(auto_error=False)


class ClerkJwtVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._jwk_client = PyJWKClient(settings.clerk_jwks_url, cache_keys=True)

    def verify(self, token: str) -> dict:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=self.settings.clerk_issuer,
            options={"verify_aud": False},
            leeway=timedelta(seconds=10),
        )
        audience = claims.get("aud")
        azp = claims.get("azp")
        expected = self.settings.clerk_audience
        audience_ok = False
        if expected:
            if isinstance(audience, str) and audience == expected:
                audience_ok = True
            elif isinstance(audience, list) and expected in audience:
                audience_ok = True
            elif azp == expected:
                audience_ok = True
        if expected and not audience_ok:
            raise jwt.InvalidAudienceError("Audience mismatch")
        if not claims.get("sub"):
            raise jwt.InvalidTokenError("Missing sub")
        if "exp" in claims:
            exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
            if exp < datetime.now(UTC):
                raise jwt.ExpiredSignatureError("Token expired")
        return claims


def get_verifier(settings: Settings = Depends(get_settings)) -> ClerkJwtVerifier:
    return ClerkJwtVerifier(settings)


def require_claims(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: ClerkJwtVerifier = Depends(get_verifier),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return verifier.verify(creds.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_current_user(
    claims: dict = Depends(require_claims),
    session: Session = Depends(get_db),
) -> User:
    clerk_user_id = claims["sub"]
    email = claims.get("email")
    if email is None:
        primary = claims.get("primary_email_address")
        email = primary if isinstance(primary, str) else None
    user_id = session.execute(
        text("SELECT ensure_user(:clerk_id, :email)"),
        {"clerk_id": clerk_user_id, "email": email},
    ).scalar_one()
    set_current_user(session, str(user_id))
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=500, detail="User upsert failed")
    return user
