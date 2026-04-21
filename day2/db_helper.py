from models.models import Profile
from app import db


class DB:
    '''DB class
    '''
    def __init__(self):
        pass

    def check_profile(self, name):
        '''checks for pre-existing data
        '''
        profile = Profile.query.filter(Profile.name==name).first()

        if profile:
            return {
                "status": "success",
                "message": "Profile already exists",
                "data": self.to_dict(profile)['data']
            }
        return None
    

    def add_profile(self, kwargs):
        '''add profile
        '''
        if not kwargs:
            return None

        
        new_profile = Profile(**kwargs)
        
        db.session.add(new_profile)
        db.session.commit()

        return self.to_dict(new_profile)
    
    def del_profile(self, id):
        '''delete profile from db
        '''
        profile = Profile.query.get(id)

        if profile:
            db.session.delete(profile)
            db.session.commit()
        else:
            return 0


    def get_profile(self, id):
        '''get profile by id
        '''

        if not id:
            return None
        
        profile = Profile.query.get(id)

        if not profile:
            return None
        
        return self.to_dict(profile)
    

    def get_profiles(self, params):
        '''get all profiles with or without filters
        '''
        if params is None or params == {}:
            profiles = Profile.query.all()
            return self.to_dict(profiles)
        

        allowed_params = ['gender', 'age_group', 'country_id', 'min_age', 'max_age',\
                          'min_gender_probability', 'min_country_probability',\
                            'sort_by', 'order', 'page', 'limit']
        
        if not all(i in allowed_params for i in params.keys()):
            return 422

        query = Profile.query

        # Apply filters only if param is provided
        # get query params
        gender                 = params.get("gender")
        age_group              = params.get("age_group")
        country_id             = params.get("country_id")
        min_age                = params.get("min_age")
        max_age                = params.get("max_age")
        min_gender_probability = params.get("min_gender_probability")
        min_country_probability= params.get("min_country_probability")

        if gender:
            query = query.filter(Profile.gender.ilike(gender))  # case-insensitive

        if country_id:
            query = query.filter(Profile.country_id.ilike(country_id))  # case-insensitive

        if age_group:
            query = query.filter(Profile.age_group.ilike(age_group))  # case-insensitive

        
        try:
            if min_age:
                query = query.filter(Profile.age >= int(min_age)) 

            if max_age:
                query = query.filter(Profile.age <= int(max_age))

            if min_gender_probability:
                query = query.filter(Profile.gender_probability >= float(min_gender_probability))

            if min_country_probability:
                query = query.filter(Profile.country_probability >= float(min_country_probability))          

        except ValueError:
            return 422
        
        # sorting
        sort_fields = {
            "age":  Profile.age,
            "created_at": Profile.created_at,
            "gender_probability": Profile.gender_probability,
        }

        order_fields = ['asc', 'desc']

        sort_by = params.get("sort_by", "created_at")
        order = params.get("order", "asc")

        if sort_by not in sort_fields \
            or order not in order_fields:
            return 422
                
        sort_column = sort_fields[sort_by]
        
        # pagination
        page = params.get("page", 1)
        limit = params.get("limit", 10)

        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            return 422
        
        # enforce max limit
        if limit > 50:
            limit = 50
        
        profiles = query.order_by(
            sort_column.asc() if order == "asc" else sort_column.desc()
            ).paginate(page=page, per_page=limit, error_out=False)
        
        return {
            "status": "success",
            "page": profiles.page,
            "limit": profiles.per_page,
            "total": profiles.total,
            "data": self.to_dict(profiles.items)
        }
    
    def to_dict(self, profile):
        '''converts python model to dict'''
        if type(profile) == list:
            profile_data = []
            for i in profile:
                profile_data.append({
                    "id": i.id,
                    "name": i.name,
                    "gender": i.gender,
                    "age": i.age,
                    "age_group": i.age_group,
                    "country_id": i.country_id
                })
        
        else:
            profile_data = {
                "data": {
                    "id": profile.id,
                    "name": profile.name,
                    "gender": profile.gender,
                    "gender_probability": profile.gender_probability,
                    # "sample_size": profile.sample_size,
                    "age": profile.age,
                    "age_group": profile.age_group,
                    "country_id": profile.country_id,
                    "country_name": profile.country_name,
                    "country_probability": profile.country_probability,
                    "created_at": profile.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                }
        
        return profile_data
