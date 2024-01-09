"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes
from app import app

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        Likes.query.delete()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_new_user(self):
        user = User.signup(username='testuser', email='test@test.com', password='testpassword', image_url=None)
        db.session.commit()

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@test.com')
        self.assertNotEqual(user.password, 'testpassword')  # password should be hashed, it should not be equal to the original password

    def test_password_verification(self):
        user = User.signup(username='testuser', email='test@test.com', password='testpassword', image_url=None)
        db.session.commit()

        self.assertTrue(user.check_password('testpassword'))  # it should return True for correct password
        self.assertFalse(user.check_password('wrongpassword'))  # it should return False for incorrect password

    def test_user_repr(self):
        user = User.signup(username='testuser', email='test@test.com', password='testpassword', image_url=None)
        db.session.commit()

        self.assertEqual(repr(user), f'<User #{user.id}: {user.username}, {user.email}>')

    def test_is_following(self):
        user1 = User(username='testuser1', email='test1@test.com', password='testpassword')
        user2 = User(username='testuser2', email='test2@test.com', password='testpassword')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        user1.following.append(user2)
        db.session.commit()

        self.assertTrue(user1.is_following(user2))  # it should return True
        self.assertFalse(user2.is_following(user1))  # it should return False

    def test_is_followed_by(self):
        user1 = User(username='testuser1', email='test1@test.com', password='testpassword')
        user2 = User(username='testuser2', email='test2@test.com', password='testpassword')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        user1.followers.append(user2)
        db.session.commit()

        self.assertTrue(user1.is_followed_by(user2))  # it should return True
        self.assertFalse(user2.is_followed_by(user1))  # it should return False
    def test_user_create_with_invalid_credentials(self):
        """Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        User.signup(username='testuser', email='test@test.com', password='testpassword', image_url=None)
        db.session.commit()

        invalid_user = User.signup(username='testuser', email='test2@test.com', password='testpassword', image_url=None)
        with self.assertRaises(Exception):  # it should raise an exception because the username is not unique
            db.session.commit()

        invalid_user = User.signup(username=None, email='test3@test.com', password='testpassword', image_url=None)
        with self.assertRaises(Exception):  # it should raise an exception because the username is None
            db.session.commit()

    def test_user_authenticate_with_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        User.signup(username='testuser', email='test@test.com', password='testpassword', image_url=None)
        db.session.commit()

        self.assertFalse(User.authenticate(username='invalidusername', password='testpassword'))  # it should return False because the username is invalid