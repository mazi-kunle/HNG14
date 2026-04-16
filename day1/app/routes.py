from flask import Blueprint, jsonify, request
from extensions import *
from db_helper import DB


# create blueprint
main = Blueprint("main", __name__, url_prefix='/api')

@main.route("/") #root route
def home():
    return "Hello World!"


@main.route("/profiles", methods=['GET', 'POST']) #/api/profiles route
def post_profiles():

    if request.method == 'GET':
        profiles = DB().get_profiles(request.args)

        if profiles is None:
            return jsonify({"status": "error", "message": "Profiles not found"}), 404
        
        return jsonify(profiles), 200
        

    data = request.get_json()
    # extract query param: name
    name = data.get("name")

    # check if name exists
    if not name or len(name) == 0:
        return jsonify({"status": "error", "message": "Bad Request"}), 400      

    # check if name is numeric
    try:
        float(name)
    except  ValueError:
        pass
    else:
        return jsonify({
            "status": "error",
            "message": "Unprocessable Entity"
        }), 422

    check_data = DB().check_profile(name)
    if check_data:
        return jsonify(check_data), 201

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
        "sample_size": g_data.get('sample_size'),
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


@main.route('/profiles/<id>', methods=['GET', 'DELETE'])
def get_profile(id):
    profile = DB()
    if request.method == 'GET':
        profile = profile.get_profile(id)   
        if not profile:
            return jsonify({
                "status": "error",
                "message": "Profile not found"
            }), 404
        
        return jsonify(profile), 200
    
    deleted_profile = profile.del_profile(id)

    if deleted_profile == 0:
        return jsonify({
            "status": "error",
            "message": "Profile not found"
        }), 404
    
    return "", 204
