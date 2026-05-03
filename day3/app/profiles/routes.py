import csv
import io
from flask import Blueprint, jsonify, request, make_response, g
from app.utils.extensions import *
from app.utils.db_helper import DB
from app.utils.nlp_parser import parse_query
from app.middleware.auth import require_auth, require_role,require_api_version
from app import limiter


# create blueprint
profile = Blueprint("profile", __name__, url_prefix='/api')

@profile.route("/") #root route
def home():
    return "Hello World!"


@profile.route("/profiles", methods=['GET']) #/api/profiles route
@require_auth
@require_api_version
@require_role("admin", "analyst")
@limiter.limit('60 per minute')
def get_profiles():
    profiles = DB().get_profiles(request.args)

    if profiles is None:
        return jsonify({"status": "error", "message": "Profiles not found"}), 404
    
    elif profiles == 422:
        return jsonify({"status": "error", "message": "Invalid query parameters"}), 422
    
    return jsonify(profiles), 200


@profile.route("/profiles", methods=['POST']) #/api/profiles route
@require_auth
@require_api_version
@require_role("admin")
@limiter.limit('60 per minute')
def create_profiles():
    data = request.get_json()
    # extract query param: name
    name = data.get("name")

    # check if name exists
    if not name or len(name) == 0:
        return jsonify({"status": "error", "message": "Missing or empty parameter"}), 400      

    # check if name is numeric
    try:
        float(name)
    except  ValueError:
        pass
    else:
        return jsonify({
            "status": "error",
            "message": "Invalid parameter type"
        }), 422

    # indenpodency check
    check_data = DB().check_profile(name)
    if check_data:
        return jsonify(check_data), 200

    # consume genderize api
    g_data = genderize(name) 

    # check that the request was sent successfully
    if g_data['status'] == "502":
        return jsonify(g_data), 502
    
    # consume agify api
    a_data = agify(name) 

    # check that the request was sent successfully
    if a_data['status'] == "502":
        return jsonify(a_data), 502

    # consume nationalize api
    n_data = nationalize(name) 

    # check that the request was sent successfully
    if n_data['status'] == "502":
        return jsonify(n_data), 502

    data = {
        "name": name,
        "gender": g_data.get('gender'),
        "gender_probability": g_data.get('gender_probability'),
        # "sample_size": g_data.get('sample_size'),
        "age": a_data.get('age'),
        "age_group": a_data.get('age_group'),
        "country_id": n_data.get('country_id'),
        "country_probability": n_data.get('country_probability')

    }

    new_data = DB().add_profile(data)

    if new_data:
        return jsonify(new_data), 201
    
    return jsonify({
        "status": "error",
        "message": "error"
    }), 502


@profile.route('/profiles/<id>', methods=['GET'])
@require_auth
@require_api_version
@require_role("admin", "analyst")
@limiter.limit('60 per minute')
def get_profile(id):
    profile = DB()
    profile = profile.get_profile(id)
    if not profile:
        return jsonify({
            "status": "error",
            "message": "Profile not found"
        }), 404
    
    return jsonify({
        "status": 'success',
        "data": profile.get('data')
    }), 200
    

@profile.route('/profiles/<id>', methods=['DELETE'])
@require_auth
@require_api_version
@require_role("admin")
@limiter.limit('60 per minute')
def del_profile(id):
    deleted_profile = profile.del_profile(id)

    if deleted_profile == 0:
        return jsonify({
            "status": "error",
            "message": "Profile not found"
        }), 404
    
    return "", 204


@profile.route("/profiles/search", methods=['GET'])
@require_auth
@require_api_version
@require_role("admin", "analyst")
@limiter.limit('60 per minute')
def get_searched_profiles():
    query = request.args.get('q', '')
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 10)

    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Missing or empty parameter'}), 400
    
    filters = parse_query(query)

    if filters:
        filters.update({'page': page, 'limit': limit})
    else:
        return jsonify({"status": "error", "message": "Invalid query parameters"}), 422

    profiles = DB().get_profiles(filters)

    if profiles is None:
        return jsonify({"status": "error", "message": "Profiles not found"}), 404
        
    elif profiles == 422:
        return jsonify({"status": "error", "message": "Invalid query parameters"}), 422
        
    return jsonify(profiles), 200
        

@profile.route("/profiles/export", methods=['GET'])
@require_auth
@require_api_version
@require_role("admin", "analyst")
@limiter.limit('60 per minute')
def export_profiles():
    """
    Exports profiles as a CSV file.
    Supports same filters as GET /profiles.
    """
    args = request.args.to_dict()
    args['limit'] = 100000
    args['page'] = 1

    export_format = request.args.get("format", "csv")

    if export_format != "csv":
        return jsonify({
            "status": "error",
            "message": "Only csv format is supported"
        }), 400
    
    profiles = DB().get_profiles(args)

    if profiles is None:
        return jsonify({"status": "error", "message": "Profiles not found"}), 404
    
    elif profiles == 422:
        return jsonify({"status": "error", "message": "Invalid query parameters"}), 422
    
    # return jsonify(profiles), 200

    data = profiles.get("data", profiles)
    # Define CSV columns in order specified by TRD
    columns = [
        "id", "name", "gender", "gender_probability",
        "age", "age_group", "country_id", "country_name",
        "country_probability", "created_at"
    ]
    # Write CSV to memory
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction="ignore"   # ignore any extra fields not in columns
    )
    writer.writeheader()
    writer.writerows(data)

    # Build response
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"profiles_{timestamp}.csv"

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return response, 200


@profile.route("/whoami")
@require_auth
def whoami():
    """Returns current logged in user info."""
    return jsonify({
        "status": 'success',
        "data": g.user.to_dict()
    })