from uuid_extensions import uuid7str
from datetime import datetime, timezone
from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=uuid7str)
    github_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255))
    avatar_url = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False, default='analyst')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    refresh_token = db.Column(db.String(500))
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime,
                           nullable=False, 
                           default=lambda: datetime.now(timezone.utc).replace(microsecond=0))

    
    def to_dict(self):
        return {
            "id": self.id,
            "github_id": self.github_id,
            "username": self.username,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "is_active": self.is_active,
            "last_login_at": (
                self.last_login_at.isoformat()
                if self.last_login_at else None
            ),
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
