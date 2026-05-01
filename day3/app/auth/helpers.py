import hashlib
import base64
import secrets
import jwt
from flask import current_app
from datetime import datetime, timezone, timedelta


#  PKCE HELPERS

def generate_code_verifier():
    '''
    Generates a random code verifier for PKCE.
    This is used by the CLI before initiating login.
    '''
    return secrets.token_urlsafe(64)



def generate_code_challenge(code_verifier):
    """
    Derives the code challenge from the code verifier.
    SHA256 hash → base64url encoded (no padding).
    This is what gets sent to GitHub.
    """
    digest = hashlib.sha256(code_verifier.encode()).digest()

    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()



def verify_code_challenge(code_verifier, code_challenge):
    """
    Verifies that a code verifier matches a code challenge.
    Called when the CLI sends code + code_verifier to our backend.
    """
    expected = generate_code_challenge(code_verifier)
    return expected == code_challenge



# TOKEN HELPERS

def generate_access_token(user_id: int, username: str, role: str) -> str:
    """
    Creates a short-lived JWT access token.
    Contains user identity and role.
    Expires in 3 minutes.
    """
    payload = {
        "sub": user_id,                    # subject — who this token belongs to
        "username": username,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),  # issued at
        "exp": datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config["ACCESS_TOKEN_EXPIRY"]
        )
    }
    token = jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    return token.decode('utf-8') if isinstance(token, bytes) else token

def generate_refresh_token(user_id: int) -> str:
    """
    Creates a longer-lived JWT refresh token.
    Only contains user id — used to get a new access token.
    Expires in 5 minutes.
    """
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config["REFRESH_TOKEN_EXPIRY"]
        )
    }
    token =  jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    return token.decode('utf-8') if isinstance(token, bytes) else token


def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Raises exceptions if token is expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}