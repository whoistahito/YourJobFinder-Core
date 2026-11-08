from db.models import User, SentEmail, Skill, Experience, Education
from extension import db
import uuid


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
