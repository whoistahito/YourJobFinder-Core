from extension import db
from datetime import datetime, timezone
import uuid


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String, nullable=False)
    position = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    job_type = db.Column(db.String, nullable=False)
    country_code = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_new = db.Column(db.Boolean, nullable=False, default=True)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmation_token = db.Column(db.String, nullable=True)
    login_token = db.Column(db.String, nullable=True)
    login_token_expires_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('email', 'position', 'location', name='_user_uc'),
    )

    skills = db.relationship('Skill', backref='user', lazy=True, cascade="all, delete-orphan")
    experiences = db.relationship('Experience', backref='user', lazy=True, cascade="all, delete-orphan")
    educations = db.relationship('Education', backref='user', lazy=True, cascade="all, delete-orphan")


class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    skill = db.Column(db.String, nullable=False)


class Experience(db.Model):
    __tablename__ = 'experiences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    experience = db.Column(db.String, nullable=False)


class Education(db.Model):
    __tablename__ = 'educations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    education = db.Column(db.String, nullable=False)



class SentEmail(db.Model):
    __tablename__ = 'sent_email'
    email = db.Column(db.String, primary_key=True)
    job_url = db.Column(db.String, primary_key=True)
    position = db.Column(db.String, primary_key=True)
    location = db.Column(db.String, primary_key=True)
