import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes
from app import app
from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1", email="test1@test.com", password="testpassword", image_url=None)
        self.testuser2 = User.signup(username="testuser2", email="test2@test.com", password="testpassword", image_url=None)
        db.session.commit()

    def tearDown(self):
        """Rollback problems that occurred during tests."""

        db.session.rollback()

    def test_repr(self):
        """Does the repr method work as expected?"""
        self.assertEqual(repr(self.testuser1), f"<User #{self.testuser1.id}: {self.testuser1.username}, {self.testuser1.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        self.testuser1.following.append(self.testuser2)
        db.session.commit()

        self.assertIn(self.testuser2, self.testuser1.following)
        self.assertTrue(self.testuser1.is_following(self.testuser2))

    def test_is_not_following(self):
        """Does is_following successfully detect when user1 is not following user2?"""
        self.assertNotIn(self.testuser2, self.testuser1.following)
        self.assertFalse(self.testuser1.is_following(self.testuser2))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        self.testuser1.followers.append(self.testuser2)
        db.session.commit()

        self.assertIn(self.testuser2, self.testuser1.followers)
        self.assertTrue(self.testuser1.is_followed_by(self.testuser2))

    def test_is_not_followed_by(self):
        """Does is_followed_by successfully detect when user1 is not followed by user2?"""
        self.assertNotIn(self.testuser2, self.testuser1.followers)
        self.assertFalse(self.testuser1.is_followed_by(self.testuser2))

    def test_user_create(self):
        """Does User.create successfully create a new user given valid credentials?"""
        user = User.signup("testuser3", "test3@test.com", "testpassword", None)
        db.session.commit()

        found_user = User.query.filter_by(username="testuser3").first()
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.email, "test3@test.com")

    def test_user_create_fail(self):
        """Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""
        with self.assertRaises(IntegrityError):
            invalid_user = User.signup(None, "test4@test.com", "testpassword", None)
            db.session.commit()

    def test_user_authenticate_success(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""
        user = User.authenticate(self.testuser1.username, "testpassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.testuser1.id)

    def test_user_authenticate_fail_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        self.assertFalse(User.authenticate("invalidusername", "testpassword"))

    def test_user_authenticate_fail_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""
        self.assertFalse(User.authenticate(self.testuser1.username, "invalidpassword"))