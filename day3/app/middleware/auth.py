from functools import wraps
from flask import request, jsonify, g
from app.auth.helpers import decode_token
from app.models.user import User

# VERIFY TOKEN
def require_auth(f):
    """
    Decorator that protects any route that requires authentication.
    
    Usage:
        @profiles_bp.route("/profiles")
        @require_auth
        def get_profiles():
            ...

    What it does:
        - Reads the Authorization header
        - Decodes and validates the token
        - Loads the user from the database
        - Stores user in Flask's g object so routes can access it
        - Rejects inactive users
    
    g is Flask's request context object.
    Think of it as a temporary bag that lives for one request only.
    You put things in it in middleware, pick them up in the route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # check auth header exists
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Authorization header is missing"
            }), 401
        
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "status": "error",
                "message": "Authorization header must be: Bearer <token>"
            }), 401
        
        token = parts[1]

        result = decode_token(token)
        if not result["valid"]:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 401
        
        payload = result['payload']
        if payload.get("type") != "access":
            return jsonify({
                "status": "error",
                "message": "Invalid token type"
            }), 401
                # Load user from database
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
        
        # Store user in g so routes can access it
        # Any route decorated with @require_auth can do g.user
        g.user = user

        return f(*args, **kwargs)
    return decorated


# ENFORCE ROLES

def require_role(*roles):
    """
    Decorator that restricts a route to specific roles.
    Must be used AFTER @require_auth since it depends on g.user.

    Usage:
        @profiles_bp.route("/profiles", methods=["POST"])
        @require_auth
        @require_role("admin")
        def create_profile():
            ...

        @profiles_bp.route("/profiles")
        @require_auth
        @require_role("admin", "analyst")
        def get_profiles():
            ...
    """
    def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if g.user.role not in roles:
                    return jsonify({
                        "status": "error",
                        "message": f"Access denied. Required role: {', '.join(roles)}"
                    }), 403
                return f(*args, **kwargs)
            return decorated
    return decorator



# VERIFY API VERSION

def require_api_version(f):
    """
    Decorator that enforces the X-API-Version header on all /api/* routes.
    
    Every request to /api/* must include:
        X-API-Version: 1

    Usage:
        @profiles_bp.route("/profiles")
        @require_auth
        @require_api_version
        def get_profiles():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_version = request.headers.get("X-API-Version")
        if not api_version:
            return jsonify({
                "status": "error",
                "message": "API version header required"
            }), 400

        if api_version != "1":
            return jsonify({
                "status": "error",
                "message": "Unsupported API version"
            }), 400

        return f(*args, **kwargs)
    return decorated