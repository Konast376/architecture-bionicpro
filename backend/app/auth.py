from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=True)

KEYCLOAK_ISSUER = os.getenv('KEYCLOAK_ISSUER', 'http://localhost:8080/realms/reports-realm')
KEYCLOAK_JWKS_URL = os.getenv(
    'KEYCLOAK_JWKS_URL',
    'http://keycloak:8080/realms/reports-realm/protocol/openid-connect/certs',
)
EXPECTED_AZP = os.getenv('KEYCLOAK_CLIENT_ID', 'reports-frontend')


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    username: str | None


@lru_cache(maxsize=1)
def jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(KEYCLOAK_JWKS_URL)


def current_user(credentials: HTTPAuthorizationCredentials = Security(bearer)) -> AuthenticatedUser:
    token = credentials.credentials
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            issuer=KEYCLOAK_ISSUER,
            options={'verify_aud': False},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid access token',
        ) from exc

    if claims.get('azp') != EXPECTED_AZP:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token was issued to another client',
        )

    subject = claims.get('sub')
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token does not contain subject',
        )

    username = claims.get('preferred_username')
    return AuthenticatedUser(
        subject=str(subject),
        username=str(username) if username else None,
    )
