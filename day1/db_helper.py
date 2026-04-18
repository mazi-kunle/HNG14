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
        

        query = Profile.query

        # Apply filters only if param is provided
        if params.get('gender'):
            query = query.filter(Profile.gender.ilike(params['gender']))  # case-insensitive

        if params.get('country_id'):
            query = query.filter(Profile.country_id.ilike(params['country_id']))  # case-insensitive

        if params.get('age_group'):
            query = query.filter(Profile.age_group.ilike(params['age_group']))  # case-insensitive

        profiles = query.all()

        print(profiles)

        return self.to_dict(profiles)

    
    def to_dict(self, profile):
        '''converts python model to dict'''
        if type(profile) == list:
            profile_data = {"status": "success", "count": len(profile), "data": []}
            for i in profile:
                profile_data['data'].append({
                    "id": i.id,
                    "name": i.name,
                    "gender": i.gender,
                    "age": i.age,
                    "age_group": i.age_group,
                    "country_id": i.country_id
                })
        
        else:
            profile_data = {
                "status": "success",
                "data": {
                    "id": profile.id,
                    "name": profile.name,
                    "gender": profile.gender,
                    "gender_probability": profile.gender_probability,
                    "sample_size": profile.sample_size,
                    "age": profile.age,
                    "age_group": profile.age_group,
                    "country_id": profile.country_id,
                    "country_probability": profile.country_probability,
                    "created_at": profile.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                }
        
        return profile_data
