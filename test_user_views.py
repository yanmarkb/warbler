import os
from unittest import TestCase
from models import db, connect_db, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all() 
        db.create_all()  

        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser", email="test@test.com", password="testpassword", image_url=None)
        self.another_user = User.signup(username="anotheruser", email="another@test.com", password="anotherpassword", image_url=None)

        db.session.commit()

        self.testuser_id = self.testuser.id
        self.another_user_id = self.another_user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        return self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)

    def logout(self):
        with self.client.session_transaction() as sess:
            if CURR_USER_KEY in sess:
                del sess[CURR_USER_KEY]
        return self.client.get('/logout', follow_redirects=True)

    def test_user_signup(self):
        with self.client as c:
            response = c.post('/signup', data=dict(
                username='newuser',
                email='new@test.com',
                password='newpassword',
                image_url=None
            ), follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)

    def test_user_login(self):
        with self.client as c:
            response = self.login()
            self.assertEqual(response.status_code, 200)

    def test_user_logout(self):
        with self.client as c:
            self.login()
            response = self.logout()
            self.assertEqual(response.status_code, 200)

    def test_user_followers_when_logged_in(self):
        self.login()
        response = self.client.get(f'/users/{self.testuser_id}/followers') 
        self.assertEqual(response.status_code, 200)

    def test_user_followers_when_logged_out(self):
        self.logout()
        response = self.client.get(f'/users/{self.testuser_id}/followers')
        self.assertNotEqual(response.status_code, 200)

    def test_user_following_when_logged_in(self):
        self.login()
        response = self.client.get(f'/users/{self.testuser_id}/following') 
        self.assertEqual(response.status_code, 200)

    def test_user_following_when_logged_out(self):
        self.logout()
        response = self.client.get(f'/users/{self.testuser_id}/following')
        self.assertNotEqual(response.status_code, 200)

    def test_user_profile_when_logged_in(self):
        self.login()
        response = self.client.get(f'/users/{self.testuser_id}') 
        self.assertEqual(response.status_code, 200)

    def test_user_profile_when_logged_out(self):
        self.logout()
        response = self.client.get(f'/users/{self.testuser_id}')
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()