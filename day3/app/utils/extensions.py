import requests


def genderize(name):
    '''
    send a request to the genderize API
    with name as the params
    '''
    api = "https://api.genderize.io"
    payload = {'name': name}

    r = requests.get(api, params=payload)

    if r.status_code != 200:
        return {
             "status": "502",
             "message": f'{api} returned an invalid response'
        }
    
    r_data = r.json()

    # extract details
    gender = r_data['gender']
    count = r_data['count']
    gender_probability = r_data['probability']

    if gender is None or count == 0:
        return {
             "status": "502",
             "message": f'{api} returned an invalid response'
        }
    
    return {
        "status": "200",
        "name": name,
        "gender": gender,
        "gender_probability": gender_probability,
        "sample_size": count   
    }

def agify(name):
    '''
    '''
    api = 'https://api.agify.io'

    payload = {'name': name}
    
    r = requests.get(api, params=payload)

    if r.status_code != 200:
        return {
            "status": "502",
            "message": f'{api} returned an invalid response'
        }
    r_data = r.json()
    # extract details
    age = r_data["age"]
    
    if age is None:
        return {
             "status": "502",
             "message": f'{api} returned an invalid response'
        }
    
    if age >= 0 and age <= 12:
        age_group = "child"
    elif age >= 13 and age <= 19:
        age_group = "teenager"
    elif age >= 20 and age <= 59:
        age_group = "adult"
    else:
        age_group = "senior"
    
    return {
        "status": "200",
        "age": age,
        "age_group": age_group
    }


def nationalize(name):
    '''
    '''
    api = 'https://api.nationalize.io'

    payload = {'name': name}
    
    r = requests.get(api, params=payload)

    if r.status_code != 200:
        return {
            "status": "502",
            "message": f'{api} returned an invalid response'
        }
    r_data = r.json()

    if  r_data.get('country') is None or r_data.get('country') == []:
        return {
             "status": "502",
             "message": f'{api} returned an invalid response'
        }
    
    country = max(r_data['country'], key=lambda x: x['probability'])

    country_prob = round(country['probability'], 2)

    return {
        'status': '200',
        'country_id': country['country_id'],
        'country_probability': country_prob
    }