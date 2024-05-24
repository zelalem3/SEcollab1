from flask import Flask, render_template, request, redirect, url_for, flash

import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey,Table
from sqlalchemy.orm import relationship



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key_here"
db = SQLAlchemy(app)

class LikedBlog(db.Model):
    __tablename__ = 'liked_blogs'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    blog_id = Column(Integer, ForeignKey('blogs.id'), primary_key=True)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True)
    username = Column(String)
    fname = Column(String(30), nullable=False)
    lname = Column(String(30), nullable=False)
    profile_photo = Column(String)
    about_me = Column(String, nullable=False)
    phone_number = Column(String(11), nullable=False)
    age = Column(String(11), nullable=False)
    status = Column(String, nullable=False)
    skills = Column(String, nullable=False)
    portfolio = Column(String)
    password = Column(String(100))
    date = Column(String, nullable=False, default=datetime.date.today().strftime("%B %d, %Y"))
    is_active = db.Column(db.Boolean, default=True)
    country = Column(String, nullable=False)
    City = Column(String, nullable=False)
    twitter = Column(String)
    github = Column(String)
    education_status = Column(String)
    employment_status=Column(String, nullable=False)
    blogs = relationship("Blog", back_populates="author")
    comments = relationship("Userscomment", back_populates="user")
    liked_blogs = relationship("Blog", secondary='liked_blogs', backref='liking_users')
    collabration = relationship("Collabration", back_populates="user")
    followers = relationship("Follower", foreign_keys="[Follower.user_id]",back_populates="followed_user")
    following = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower")
    interests = relationship("Interest", back_populates="user")
class Follower(db.Model):
    __tablename__ = "followers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    follower_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    followed_user = relationship("User", foreign_keys=[user_id], back_populates="followers")
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")


class Blog(db.Model):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    content = Column(String, nullable=False)
    blog_image = Column(String)
    like = Column(Integer, nullable=False, default=0)
    date = Column(String, default=datetime.date.today().strftime("%B %d, %Y"))

    author = relationship("User", back_populates="blogs")
    user = relationship("User", back_populates="blogs")


team_members = Table('team_members', db.Model.metadata,
    Column('project_id', Integer, ForeignKey('collabration.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)
class Collabration(db.Model):
    __tablename__ = "collabration"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    uploaded_date = Column(String, nullable=False, default=datetime.date.today().strftime("%B %d, %Y"))
    requirment = Column(String, nullable=False)
    Looking_for = Column(String, nullable=False)
    due_date = Column(String)
    members = relationship("User", secondary=team_members, backref="teams")
    user = relationship("User", back_populates="collabration")
    interests = relationship("Interest", back_populates="collabration")




class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    message = db.Column(db.String)


class Userscomment(db.Model):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(String, nullable=False)
    user = relationship("User", back_populates="comments")


class Interest(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('collabration.id'), nullable=False)

    user = relationship("User", back_populates="interests")
    collabration = relationship("Collabration", back_populates="interests")



with app.app_context():

    db.create_all()
