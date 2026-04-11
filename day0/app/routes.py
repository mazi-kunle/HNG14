from flask import Blueprint, jsonify, request
import requests
from datetime import datetime, timezone


# create blueprint
main = Blueprint("main", __name__)


@main.route("/api/classify", methods=['GET']) #/api/classify route
def classify():
    # extract query param: name
    name = request.args.get("name")

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

    
    api = "https://api.genderize.io"
    payload = {'name': name}

    r = requests.get(api, params=payload) # consume genderize api
    # check that the request was sent successfully
    if r.status_code != 200:
          return jsonify({
                "status": "error",
                "message": "Upstream API server error"
          }), 502
          
    r_data = r.json()

    # extract details
    gender = r_data['gender']
    sample_size = r_data['count']

    if gender is None or sample_size == 0: # check if gender is Null or count = 0
         return jsonify({
              "status": "error",
                "message": "No prediction available for the provided name"
         }) 
    
    probability = r_data['probability']
    is_confident = probability >= 0.7 and sample_size >= 100
    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return jsonify({
         "status": "success",
         "data" : {
              "name": name,
              "gender": gender,
              "probability": probability,
              "sample_size": sample_size,
              "is_confident": is_confident,
              "processed_at": utc_now
         }
    })
