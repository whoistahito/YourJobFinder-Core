from db.models import User, SentEmail, Skill, Experience, Education
from extension import db
from sqlalchemy import func
from datetime import datetime, timezone
import uuid


def _utcnow() -> datetime:
    # naive UTC so comparisons match the naive DateTime column
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserManager:
    def add_user(self, email, position, location, job_type, country_code=None, skills=None, experience=None, education=None):
        token = str(uuid.uuid4())
        user = User(email=email, position=position, location=location, job_type=job_type, country_code=country_code, confirmation_token=token)
        if skills:
            for s in skills:
                user.skills.append(Skill(skill=s))
        if experience:
            for e in experience:
                user.experiences.append(Experience(experience=e))
        if education:
            for ed in education:
                user.educations.append(Education(education=ed))

        if not self.user_exists(email, position, location):
            db.session.add(user)
            db.session.commit()
            return user
        return None

    def delete_user(self, email, position, location):
        user = self.user_exists(email=email, position=position, location=location)
        if user:
            db.session.delete(user)
            db.session.commit()

    def user_exists(self, email, position, location):
        return (User.query
                .filter_by(email=email, position=position, location=location).one_or_none())

    def get_user(self, user_id: str):
        """Look up a user by primary key (dashboard API), or None."""
        return User.query.filter_by(id=user_id).first() if user_id else None

    def get_new_users(self):
        return User.query.filter_by(is_new=True).all()

    def mark_user_as_not_new(self, email, position, location):
        user = self.user_exists(email=email, position=position, location=location)
        if user:
            user.is_new = False
            db.session.commit()

    def get_all_users(self):
        return User.query.all()

    def confirm_user(self, token):
        user = User.query.filter_by(confirmation_token=token).first()
        if user:
            user.is_confirmed = True
            user.confirmation_token = None
            db.session.commit()
            return user
        return None

    def find_users_by_email(self, email):
        """All subscriptions for an email, newest first (emails are not unique)."""
        return (User.query
                .filter(func.lower(User.email) == (email or '').strip().lower())
                .order_by(User.created_at.desc())
                .all())

    def set_login_token(self, user_id, token, expires_at):
        user = self.get_user(user_id)
        if not user:
            return None
        user.login_token = token
        user.login_token_expires_at = expires_at
        db.session.commit()
        return user

    def consume_login_token(self, token):
        """Single magic-link use: valid+unexpired row is cleared and returned."""
        user = User.query.filter_by(login_token=token).one_or_none()
        if not user:
            return None
        valid = user.login_token_expires_at is not None and user.login_token_expires_at >= _utcnow()
        user.login_token = None
        user.login_token_expires_at = None
        db.session.commit()
        return user if valid else None

    def get_confirmed_users(self):
        return User.query.filter_by(is_confirmed=True).all()


class UserEmailManager:
    def add_sent_email(self, email, job_url, position, location):
        user = SentEmail(email=email, job_url=job_url, position=position, location=location)
        db.session.add(user)
        db.session.commit()

    def is_sent(self, email, job_url, position, location):
        return SentEmail.query.filter_by(email=email, job_url=job_url, position=position,
                                         location=location).count() > 0
