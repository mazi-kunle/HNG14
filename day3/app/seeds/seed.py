from app import create_app, db
from app.models.profile import Profile
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = create_app()

with open(os.path.join(BASE_DIR, "seed_profiles.json")) as f:
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