import os
from unittest import TestCase
from models import db, connect_db, User

# I'm setting the environment variable for the database URL to use the test database.
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# I'm importing the app and the current user key from the app module.
from app import app, CURR_USER_KEY

# I'm disabling CSRF protection for the tests.
app.config['WTF_CSRF_ENABLED'] = False

# I'm defining a test case for user views.
class UserViewTestCase(TestCase):
    """Test views for users."""

    # I'm defining the setup method to create a test client and add sample data.
    def setUp(self):
        """Create test client, add sample data."""

        # I'm dropping all tables in the database and creating them again.
        db.drop_all() 
        db.create_all()  

        # I'm deleting all users from the database.
        User.query.delete()

        # I'm creating a test client.
        self.client = app.test_client()

        # I'm signing up two users and saving them to the database.
        self.testuser = User.signup(username="testuser", email="test@test.com", password="testpassword", image_url=None)
        self.another_user = User.signup(username="anotheruser", email="another@test.com", password="anotherpassword", image_url=None)

        # I'm committing the session to save the new users to the database.
        db.session.commit()

        # I'm storing the IDs of the users for later use.
        self.testuser_id = self.testuser.id
        self.another_user_id = self.another_user.id

    # I'm defining the teardown method to clean up after each test.
    def tearDown(self):
        # I'm removing the current session and dropping all tables in the database.
        db.session.remove()
        db.drop_all()

    # I'm defining a method to log in a user by sending a POST request to the login route with the user's credentials.
    def login(self):
        return self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)

    # I'm defining a method to log out a user by deleting the current user key from the session and sending a GET request to the logout route.
    def logout(self):
        with self.client.session_transaction() as sess:
            if CURR_USER_KEY in sess:
                del sess[CURR_USER_KEY]
        return self.client.get('/logout', follow_redirects=True)

    # I'm defining a test method to test user signup.
    def test_user_signup(self):
        with self.client as c:
            # I'm sending a POST request to the signup route with the new user's data.
            response = c.post('/signup', data=dict(
                username='newuser',
                email='new@test.com',
                password='newpassword',
                image_url=None
            ), follow_redirects=True)

            # I'm asserting that the response status code is 200, which means the request was successful.
            self.assertEqual(response.status_code, 200)

            # I'm querying the database for the new user.
            user = User.query.filter_by(username='newuser').first()

            # I'm asserting that the new user exists in the database.
            self.assertIsNotNone(user)

    # I'm defining a test method to test user login.
    def test_user_login(self):
        with self.client as c:
            # I'm logging in a user.
            response = self.login()

            # I'm asserting that the response status code is 200, which means the request was successful.
            self.assertEqual(response.status_code, 200)

    # I'm defining a test method to test user logout.
    def test_user_logout(self):
        with self.client as c:
            # I'm logging in a user.
            self.login()

            # I'm logging out the user.
            response = self.logout()

            # I'm asserting that the response status code is 200, which means the request was successful.
            self.assertEqual(response.status_code, 200)

    # I'm defining a test method to test viewing the followers of a user when logged in.
    def test_user_followers_when_logged_in(self):
        # I'm logging in a user.
        self.login()

        # I'm sending a GET request to the followers route.
        response = self.client.get(f'/users/{self.testuser_id}/followers') 

        # I'm asserting that the response status code is 200, which means the request was successful.
        self.assertEqual(response.status_code, 200)

    # I'm defining a test method to test viewing the followers of a user when logged out.
    def test_user_followers_when_logged_out(self):
        # I'm logging out the user.
        self.logout()

        # I'm sending a GET request to the followers route.
        response = self.client.get(f'/users/{self.testuser_id}/followers')

        # I'm asserting that the response status code is not 200, which means the request was not successful.
        self.assertNotEqual(response.status_code, 200)

    # I'm defining a test method to test viewing the users a user is following when logged in.
    def test_user_following_when_logged_in(self):
        # I'm logging in a user.
        self.login()

        # I'm sending a GET request to the following route.
        response = self.client.get(f'/users/{self.testuser_id}/following') 

        # I'm asserting that the response status code is 200, which means the request was successful.
        self.assertEqual(response.status_code, 200)

    # I'm defining a test method to test viewing the users a user is following when logged out.
    def test_user_following_when_logged_out(self):
        # I'm logging out the user.
        self.logout()

        # I'm sending a GET request to the following route.
        response = self.client.get(f'/users/{self.testuser_id}/following')

        # I'm asserting that the response status code is not 200, which means the request was not successful.
        self.assertNotEqual(response.status_code, 200)

    # I'm defining a test method to test viewing a user's profile when logged in.
    def test_user_profile_when_logged_in(self):
        # I'm logging in a user.
        self.login()

        # I'm sending a GET request to the user's profile route.
        response = self.client.get(f'/users/{self.testuser_id}') 

        # I'm asserting that the response status code is 200, which means the request was successful.
        self.assertEqual(response.status_code, 200)

    # I'm defining a test method to test viewing a user's profile when logged out.
    def test_user_profile_when_logged_out(self):
        # I'm logging out the user.
        self.logout()

        # I'm sending a GET request to the user's profile route.
        response = self.client.get(f'/users/{self.testuser_id}')

        # I'm asserting that the response status code is not 200, which means the request was not successful.
        self.assertNotEqual(response.status_code, 200)

    # I'm checking if this script is the main module and, if so, running the tests.
    if __name__ == '__main__':
        unittest.main()