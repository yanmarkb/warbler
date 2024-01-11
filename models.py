"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask import session
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import CheckConstraint


# Initialize the Bcrypt extension for hashing passwords.
bcrypt = Bcrypt()

# Initialize the SQLAlchemy extension for interacting with the database.
db = SQLAlchemy()

# Define a model for the follows relationship between users.
class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    # Set the name of the table in the database.
    __tablename__ = 'follows'

    # Define a column for the ID of the user being followed, which is a foreign key to the users table and part of the primary key for the follows table.
    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    # Define a column for the ID of the user following, which is a foreign key to the users table and part of the primary key for the follows table.
    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

# Define a model for the likes relationship between users and messages.
class Likes(db.Model):
    """Connection of a user <-> liked_message."""

    # Set the name of the table in the database.
    __tablename__ = 'likes'

    # Define a column for the ID of the like, which is the primary key for the likes table.
    id = db.Column(db.Integer, primary_key=True)

    # Define a column for the ID of the user who liked the message, which is a foreign key to the users table.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Define a column for the ID of the message that was liked, which is a foreign key to the messages table.
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))

    # Add a unique constraint to the user_id and message_id columns to ensure that a user can only like a message once.
    __table_args__ = (db.UniqueConstraint('user_id', 'message_id', name='user_message_uc'),)

# Define a model for users.
class User(db.Model):
    """User in the system."""

    # Set the name of the table in the database.
    __tablename__ = 'users'

    # Define a column for the ID of the user, which is the primary key for the users table.
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Define a column for the email of the user, which is required and must be unique.
    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    # Define a column for the username of the user, which is required and must be unique.
    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    # Define a column for the image URL of the user, which defaults to a placeholder image.
    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    # Define a column for the header image URL of the user, which defaults to a placeholder image.
    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )

    # Define a column for the bio of the user, which is optional.
    bio = db.Column(
        db.Text,
    )

    # Define a column for the location of the user, which is optional.
    location = db.Column(
        db.Text,
    )

    # Define a column for the password of the user, which is required.
    password = db.Column(
        db.Text,
        nullable=False,
    )

    # Define a relationship to the Message model to get the messages of the user.
    messages = db.relationship('Message')

    # Define a relationship to the User model through the Follows model to get the followers of the user.
    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id)
    )
    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_following_id == id),
        secondaryjoin=(Follows.user_being_followed_id == id)
    )

    likes = db.relationship('Message', secondary='likes', backref='user_likes')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [user for user in self.following if user == other_user]
        return len(found_user_list) == 1
    
    def check_password(self, password):
        """Check password against hashed version."""
        return bcrypt.check_password_hash(self.password, password)

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    @classmethod
    def logout(cls):
            """Clear the session to log out the user."""
            session.clear()  # Clear the session to log out the user.


# Define a model for messages, which is called "warbles".
class Message(db.Model):
    """An individual message ("warble")."""

    # Set the name of the table in the database.
    __tablename__ = 'messages'

    # Define a column for the ID of the message, which is the primary key for the messages table.
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Define a column for the text of the message, which is required and must be no more than 140 characters.
    text = db.Column(
        db.String(140),
        nullable=False,
    )

    # Define a column for the timestamp of the message, which defaults to the current time and is required.
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    # Define a column for the ID of the user who posted the message, which is a foreign key to the users table and is required.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Add a check constraint to ensure that the text of the message is not null.
    __table_args__ = (
        CheckConstraint(text != None, name='check_text_not_empty'),
    )

    # Define a relationship to the User model to get the user who posted the message.
    user = db.relationship('User')

# Define a function to connect the database to a Flask app.
def connect_db(app):
    """Connect this database to provided Flask app.
    """

    # Set the app attribute of the db object to the provided Flask app.
    db.app = app

    # Call the init_app method of the db object to complete the connection.
    db.init_app(app)
