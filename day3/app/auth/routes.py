import requests
from flask import Blueprint, redirect, request, jsonify, current_app
import secrets
from flask import session
from app.models.user import User
from app.utils.db_helper import DB
from app import db
from app.auth.helpers import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    verify_code_challenge,
)
from app import limiter
from datetime import datetime, timezone


auth = Blueprint("auth", __name__, url_prefix='/auth')

@auth.route('/github')
@limiter.limit('10 per minute')
def github_login():
    '''
    Web portal hits this endpoint when user clicks 'Login with GitHub'.
    CLI opens this URL directly in the browser.
    
    We redirect the user to GitHub's OAuth page.
    GitHub will ask them to approve access, then send them back to our callback.
    '''
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    client_id = current_app.config['GITHUB_CLIENT_ID']
    redirect_uri = current_app.config['GITHUB_REDIRECT_URI']

    code_challenge = request.args.get('code_challenge', "")

    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=read:user,user:email"
        f"&state={state}"
    )
    if code_challenge:
        github_auth_url += (
            f'&code_challenge={code_challenge}'
            f"&code_challenge_method=S256"
        )

    return redirect(github_auth_url)


@auth.route("/github/cli")
@limiter.limit('10 per minute')
def github_login_cli():
    """
    Specifically for CLI login.
    Uses CLI OAuth app credentials and CLI redirect URI.
    """
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    code_challenge = request.args.get("code_challenge", "").strip()

    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={current_app.config['GITHUB_CLI_CLIENT_ID']}"
        f"&redirect_uri={current_app.config['GITHUB_CLI_REDIRECT_URI']}"
        f"&scope=read:user,user:email"
        f"&state={state}"
    )

    if code_challenge:
        github_auth_url += (
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )

    return redirect(github_auth_url)



@auth.route("/github/callback")
@limiter.limit('10 per minute')
def github_callback():
    """
    GitHub redirects here after user approves access.
    URL will contain: ?code=TEMP123&state=XYZ

    For the web portal:
    - This is hit directly by the browser
    - We set HTTP-only cookies and redirect to dashboard

    For the CLI:
    - CLI's local server catches the redirect first
    - CLI then calls POST /auth/github/callback with code + code_verifier
    - So this GET endpoint is mainly for the web portal
    """
    code = request.args.get("code")
    state = request.args.get("state")
    
    # Validate state matches what we stored
    if state != session.get("oauth_state"):
        return jsonify({
            "status": "error",
            "message": "Invalid state parameter"
        }), 400
    
    if not code:
        return jsonify({
            "status": "error",
            "message": "No code received from GitHub"
        }), 400
    # Exchange code for GitHub access token
    github_token = exchange_code_for_token(code)
    if not github_token:
        return jsonify({
            "status": "error",
            "message": "Failed to exchange code with GitHub"
        }), 400

    # Get user info from GitHub
    github_user = get_github_user(github_token)
    if not github_user:
        return jsonify({
            "status": "error",
            "message": "Failed to fetch user info from GitHub"
        }), 400
    
    user = upsert_user(github_user)
    
    access_token = generate_access_token(user.id, user.username, user.role)
    refresh_token = generate_refresh_token(user.id)

    user.refresh_token = refresh_token
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    # for web portal
    return jsonify({
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


@auth.route("/github/callback", methods=["POST"])
@limiter.limit('10 per minute')
def github_callback_cli():
    """
    This is specifically for the CLI.
    CLI sends: { code, code_verifier, state }
    We verify PKCE, exchange code with GitHub, return tokens.
    """
    data = request.get_json()

    code = data.get("code")
    code_verifier = data.get("code_verifier")
    code_challenge = data.get("code_challenge")

    if not code or not code_verifier:
        return jsonify({
            "status": "error",
            "message": "code and code_verifier are required"
        }), 400

    # Verify PKCE — make sure the verifier matches the challenge
    if code_challenge and not verify_code_challenge(code_verifier, code_challenge):
        return jsonify({
            "status": "error",
            "message": "PKCE verification failed"
        }), 400
    
    # Exchange code for GitHub access token
    github_token = exchange_code_for_token(code, code_verifier, is_cli=True)

    if not github_token:
        return jsonify({
            "status": "error",
            "message": "Failed to exchange code with GitHub"
        }), 400
    
    # Get user info from GitHub
    github_user = get_github_user(github_token)
    if not github_user:
        return jsonify({
            "status": "error",
            "message": "Failed to fetch user info from GitHub"
        }), 400

    # Create or update user in our database
    user = upsert_user(github_user)

    # Generate our own tokens
    access_token = generate_access_token(user.id, user.username, user.role)
    refresh_token = generate_refresh_token(user.id)

    # Save refresh token
    user.refresh_token = refresh_token
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


@auth.route("/refresh", methods=["POST"])
@limiter.limit('10 per minute')
def refresh():
    """
    Called when access token expires.
    Sends refresh token, gets new pair back.
    Old refresh token is immediately invalidated.
    """
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({
            "status": "error",
            "message": "Refresh token is required"
        }), 400

    # Decode and validate the refresh token
    result = decode_token(refresh_token)
    if not result["valid"]:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 401

    payload = result["payload"]

    # Make sure it's actually a refresh token not an access token
    if payload.get("type") != "refresh":
        return jsonify({
            "status": "error",
            "message": "Invalid token type"
        }), 401

    # Find the user
    user = User.query.get(payload["sub"])
    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 401

    # Check if user is active
    if not user.is_active:
        return jsonify({
            "status": "error",
            "message": "Account is deactivated"
        }), 403

    # Check if this refresh token matches what we stored
    # This catches stolen/reused refresh tokens
    if user.refresh_token != refresh_token:
        print('refresh token not same')
        return jsonify({
            "status": "error",
            "message": "Refresh token has already been used or is invalid"
        }), 401

    # Generate new pair
    new_access_token = generate_access_token(user.id, user.username, user.role)
    new_refresh_token = generate_refresh_token(user.id)

    # Invalidate old refresh token by replacing it
    user.refresh_token = new_refresh_token
    db.session.commit()

    return jsonify({
        "status": "success",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }), 200


# ─── LOGOUT ───────────────────────────────────────────────────────────────────

@auth.route("/logout", methods=["POST"])
@limiter.limit('10 per minute')
def logout():
    """
    Invalidates the refresh token server-side.
    Even if someone has the token after this, it won't work.
    """
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({
            "status": "error",
            "message": "Refresh token is required"
        }), 400

    result = decode_token(refresh_token)
    if not result["valid"]:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 401

    user = User.query.get(result["payload"]["sub"])
    if user:
        # Wipe the refresh token — this logs them out everywhere
        user.refresh_token = None
        db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Logged out successfully"
    }), 200


# ─── PRIVATE HELPER FUNCTIONS ─────────────────────────────────────────────────

def exchange_code_for_token(code: str, code_verifier: str = None, is_cli=False):
    """
    Sends the code to GitHub and gets back a GitHub access token.
    This happens server to server — user never sees this.
    """
    if is_cli:
        client_id = current_app.config["GITHUB_CLI_CLIENT_ID"]
        client_secret = current_app.config["GITHUB_CLI_CLIENT_SECRET"]
        redirect_uri = current_app.config["GITHUB_CLI_REDIRECT_URI"]
    else:
        client_id = current_app.config["GITHUB_CLIENT_ID"]
        client_secret = current_app.config["GITHUB_CLIENT_SECRET"]
        redirect_uri = current_app.config["GITHUB_REDIRECT_URI"]

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    if code_verifier:
        payload["code_verifier"] = code_verifier

    response = requests.post(
        "https://github.com/login/oauth/access_token",
        json=payload,
        headers={"Accept": "application/json"}
    )

    data = response.json()
    return data.get("access_token")


def get_github_user(github_token: str):
    """
    Uses the GitHub access token to fetch the user's profile.
    Returns their id, username, email, avatar.
    """
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json"
        }
    )

    if response.status_code != 200:
        return None

    user_data = response.json()

    # Email can be private on GitHub, fetch it separately if needed
    email = user_data.get("email")
    if not email:
        email = get_github_email(github_token)

    return {
        "github_id": str(user_data["id"]),
        "username": user_data["login"],
        "email": email,
        "avatar_url": user_data.get("avatar_url")
    }


def get_github_email(github_token: str):
    """
    Fetches the user's primary email separately.
    Some GitHub users hide their email on their public profile.
    """
    response = requests.get(
        "https://api.github.com/user/emails",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json"
        }
    )

    if response.status_code != 200:
        return None

    emails = response.json()
    for email in emails:
        if email.get("primary") and email.get("verified"):
            return email["email"]

    return None


def upsert_user(github_user: dict):
    """
    Creates a new user or updates an existing one.
    We identify users by their github_id — it never changes.
    First user to sign up gets admin role, everyone else is analyst.
    """
    user = User.query.filter_by(github_id=github_user["github_id"]).first()

    if not user:
        # Check if this is the very first user — make them admin
        is_first_user = User.query.count() == 0

        user = User(
            github_id=github_user["github_id"],
            username=github_user["username"],
            email=github_user["email"],
            avatar_url=github_user["avatar_url"],
            role="admin" if is_first_user else "analyst"
        )
        db.session.add(user)
    else:
        # Update their info in case they changed it on GitHub
        user.username = github_user["username"]
        user.email = github_user["email"]
        user.avatar_url = github_user["avatar_url"]

    db.session.commit()
    return user