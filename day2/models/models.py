from uuid_extensions import uuid7str
from datetime import datetime, timezone
from app import db


class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.String(36), primary_key=True, default=uuid7str)

    name = db.Column(db.String(100), nullable=False, unique=True)
    gender = db.Column(db.String(10))
    gender_probability = db.Column(db.Float)

    # sample_size = db.Column(db.Integer)

    age = db.Column(db.Integer)
    age_group = db.Column(db.String(20))

    country_id=db.Column(db.String(2))
    country_name = db.Column(db.String(100), nullable=False)
    country_probability = db.Column(db.Float)

    created_at = db.Column(db.DateTime(),
                           nullable=False, 
                           default=lambda: datetime.now(timezone.utc).replace(microsecond=0))

    

