from bcrypt import hashpw, gensalt
from datetime import datetime
from sqlalchemy import (
    Column, Integer, TIMESTAMP, String, ForeignKey)

from . import Base, DBSession, p


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(512), nullable=False)

    def __repr__(self):
        return 'id={} email={} name={} hashed_password={}'.format(
            self.id, self.email, self.name, self.hashed_password)

    @staticmethod
    def hash_pd(password, salt=gensalt()):
        return hashpw(password.encode(), salt)

    def verify_user(self, email, password):
        user = self.get_by_email(email)
        if not user or not user.hashed_password.encode() == hashpw(
          password.encode(), user.hashed_password.encode()):
            return False
        return user

    @classmethod
    def get_by_id(cls, id):
        session = DBSession()
        info = session.query(cls).filter(cls.id == id).first()
        session.close()
        return info

    @classmethod
    def get_by_email(cls, email):
        session = DBSession()
        info = session.query(cls).filter(cls.email == email).first()
        session.close()
        return info

    @classmethod
    def get_one(cls):
        session = DBSession()
        info = session.query(cls).first()
        session.close()
        return info

    @classmethod
    def add(cls, info):
        session = DBSession()
        session.add(cls(
            email=info.get('email'),
            name=info.get('name'),
            hashed_password=info.get('hashed_password').decode(),
        ))
        try:
            session.commit()
        except Exception as e:
            p.error()
            session.rollback()
            return False
        session.close()
        return True


class Entries(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(
        Integer, ForeignKey('user.id'), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    title = Column(String(512), nullable=False)
    markdown = Column(String(512), nullable=False)
    html = Column(String(512), nullable=False)
    published = Column(TIMESTAMP, index=True, nullable=False)
    updated = Column(TIMESTAMP, nullable=False)

    @classmethod
    def get_by_slug(cls, slug):
        session = DBSession()
        info = session.query(cls).filter(cls.slug == slug).first()
        session.close()
        return info

    @classmethod
    def get_by_id(cls, id):
        session = DBSession()
        info = session.query(cls).filter(cls.id == id).first()
        session.close()
        return info

    @classmethod
    def get_all(cls):
        session = DBSession()
        info = session.query(cls).order_by(cls.published.desc()).all()
        session.close()
        return info

    @classmethod
    def add(cls, info):
        now = datetime.now()
        session = DBSession()
        session.add(cls(
            user_id=info.get('user_id'),
            slug=info.get('slug'),
            title=str(info.get('title')),
            markdown=info.get('markdown'),
            html=info.get('html'),
            published=now,
            updated=now
        ))
        try:
            session.commit()
        except Exception as e:
            p.error()
            session.rollback()
            return False
        session.close()
        return True

    @classmethod
    def update(cls, data):
        now = datetime.now()
        session = DBSession()
        info = session.query(cls).filter(cls.id == data.get('id'))
        info.update({cls.title: data['title']}) if data['title'] else None
        info.update({cls.markdown: data['markdown']}) if data['markdown'] \
            else None
        info.update({cls.html: data['html']}) if data['html'] else None
        info.update({cls.updated: now})
        try:
            session.commit()
        except Exception as e:
            p.error()
            session.rollback()
            return False
        session.close()
        return True
