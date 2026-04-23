GENDER_MAP = {
    'male': 'male', 'males':'male', 'man': 'male', 'men': 'male',
    'boy': 'male', 'boys': 'male',
    'female': 'female', 'females': 'female', 'woman': 'female', 'women': 'female',
    'girl': 'female', 'girls': 'female'
}

COUNTRY_MAP = {
    'nigeria': 'NG', 'nigerian': 'NG', 'nigerians': 'NG',
    'ghana': 'GH', 'ghanaian': 'GH', 'ghanaians': 'GH',
    'kenya': 'KE', 'kenyan': 'KE', 'kenyans': 'KE',
    'angola': 'AO', 'angolan': 'AO', 'angolans': 'AO',
    'southafrica': 'ZA', 'ethiopia': 'ET', 'ethiopia': 'ET',
    'tanzania': 'TZ', 'uganda': 'UG', 'rwanda': 'RW',
    'cameroon': 'CM', 'senegal': 'SN', 'zambia': 'ZM',
    'united states': 'US', 'united kingdom': 'UK', 'Madagascar': 'MG',
    'india': 'IN', 'cape verde': 'CV', 'congo': 'CG',
    'republic of the congo': 'CG', 'mozambique': 'MZ',
    'mali': 'ML', 'dr congo': 'CD', 'france': 'FR', 'eritrea': 'ER',
    'gabon': 'GA', 'namibia': 'NA', 'morocco': 'MA', 'malawi': 'MW',
    'brazil': 'BR', 'france': 'FR', 'benin': 'BJ', 'japan': 'JP'
}

AGE_GROUP_MAP = {
    'child':     {'age_group': 'child', 'max_age': 12},
    'children':  {'age_group': 'child', 'max_age': 12},
    'teenager':  {'age_group': 'teenager', 'min_age': 13, 'max_age': 19},
    'teenagers': {'age_group': 'teenager', 'min_age': 13, 'max_age': 19},
    'teen':      {'age_group': 'teenager', 'min_age': 13, 'max_age': 19},
    'teens':     {'age_group': 'teenager', 'min_age': 13, 'max_age': 19},
    'adult':     {'age_group': 'adult',    'min_age': 20, 'max_age': 59},
    'adults':    {'age_group': 'adult',    'min_age': 20, 'max_age': 59},
    'senior':    {'age_group': 'senior',   'min_age': 60},
    'seniors':   {'age_group': 'senior',   'min_age': 60},
    'elderly':   {'age_group': 'senior',   'min_age': 60},
}

YOUNG_KEYWORDS  = {'young', 'youth', 'youths'}
ABOVE_KEYWORDS  = {'above', 'over', 'older', 'atleast', 'minimum', 'min', 'plus'}
BELOW_KEYWORDS  = {'below', 'under', 'younger', 'atmost', 'maximum', 'max'}
FROM_KEYWORDS   = {'from', 'in', 'of'}

def parse_query(q):
    tokens = q.lower().strip().split()
    filters = {}
    used = set()

    # Gender
    genders_found = set()
    for i, token in enumerate(tokens):
        if token in GENDER_MAP:
            genders_found.add(GENDER_MAP[token])
            used.add(i)
    
    if len(genders_found) == 1:
        filters['gender'] = genders_found.pop()
    # ignore if both male and female genders are found

    #  young keyword
    young_found = False
    for i, token in enumerate(tokens):
        if token in YOUNG_KEYWORDS:
            young_found = True
            used.add(i)

    # Age groups
    for i, token in enumerate(tokens):
        if token in AGE_GROUP_MAP:
            group = AGE_GROUP_MAP[token]
            filters['age_group'] = group['age_group']
            if 'min_age' in group:
                filters['min_age'] = group['min_age']
            if 'max_age' in group:
                filters['max_age'] = group['max_age']
            used.add(i)
    
    #  young overrides age_group
    if young_found:
        filters['min_age'] = 16
        filters['max_age'] = 24
        filters.pop('age_group', None)
    
    # Directional age modifiers: "above 30", "under 18"
    for i, token in enumerate(tokens):
        if i in used:
            continue
        if token in ABOVE_KEYWORDS and i + 1 < len(tokens):
            try:
                filters['min_age'] = int(tokens[i+1])
                used.add(i)
                used.add(i+1)
            except ValueError:
                pass
        elif token in BELOW_KEYWORDS and i + 1 < len(tokens):
            try:
                filters['max_age'] = int(tokens[i + 1])
                used.add(i)
                used.add(i + 1)
            except ValueError:
                pass

    # Bare number fallback (e.g. "males 25")
    for i, token in enumerate(tokens):
        if i in used:
            continue
        try:
            num = int(token)
            if 0 < num < 120 and 'min_age' not in filters and 'max_age' not in filters:
                filters['min_age'] = num
                used.add(i)
        except ValueError:
            pass
    
    # Country
    for i, token in enumerate(tokens):
        if token in FROM_KEYWORDS and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token in COUNTRY_MAP:
                filters['country_id'] = COUNTRY_MAP[next_token]
                used.add(i)
                used.add(i+1)
        elif i not in used and token in COUNTRY_MAP:
            filters['country_id'] = COUNTRY_MAP[token]
            used.add(i)
    
    if not filters:
        return None
    
    print(used)
    return filters

