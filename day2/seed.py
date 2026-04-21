from main import app
from app import db
from models.models import Profile
import json

with open("seed_profiles.json", "r") as f:
    data = json.load(f)


with app.app_context():
    db.create_all()

    for item in data['profiles']:
        exists = Profile.query.filter_by(name=item["name"]).first()
        if not exists:
            profile = Profile(**item)
            db.session.add(profile)

    db.session.commit()
    print("Database seeded successfully.")