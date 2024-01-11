# I'm importing the os module, which allows me to interact with the operating system.
import os
# I'm importing TestCase from the unittest module, which provides a framework for creating tests.
from unittest import TestCase

# I'm importing the db, connect_db, Message, and User classes from the models module.
from models import db, connect_db, Message, User

# I'm setting an environment variable to specify the database URL for testing.
# This needs to be done before importing the app, as the app connects to the database upon import.
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now that the database URL is set, I can import the app and the current user key.
from app import app, CURR_USER_KEY

# I'm creating all the tables in the database.
# This is done here so that the tables are created once for all tests.
db.create_all()

# I'm disabling CSRF protection in WTForms for testing, as it can be difficult to test.
app.config['WTF_CSRF_ENABLED'] = False

# I'm defining a test case class for the message views.
class MessageViewTestCase(TestCase):
    """Test views for messages."""

    # In the setUp method, I'm setting up the test client and some sample data.
    def setUp(self):
        """Create test client, add sample data."""

        # I'm dropping all tables in the database and then creating them again.
        # This ensures a clean slate for each test.
        db.drop_all() 
        db.create_all()  

        # I'm deleting all users and messages from the database.
        User.query.delete()
        Message.query.delete()

        # I'm creating a test client, which allows me to send requests to the app within tests.
        self.client = app.test_client()

        # I'm signing up two users and saving them to the database.
        self.testuser = User.signup(username="testuser", email="test@test.com", password="testpassword", image_url=None)
        self.another_user = User.signup(username="anotheruser", email="another@test.com", password="anotherpassword", image_url=None)

        # I'm committing the session to save the new users to the database.
        db.session.commit()

        # I'm saving the IDs of the two users for later use in tests.
        self.testuser_id = self.testuser.id
        self.another_user_id = self.another_user.id

    # In the tearDown method, I'm cleaning up after each test.
    def tearDown(self):
        # I'm removing the current session and dropping all tables in the database.
        db.session.remove()
        db.drop_all()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # I'm querying the database for the message.
            msg = Message.query.one()
            # I'm asserting that the text of the message is "Hello".
            self.assertEqual(msg.text, "Hello")

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

            # I'm defining a test method to test viewing the followers of a user when logged in.
            def test_followers_when_logged_in(self):
                self.login()  # I'm logging in a user.
                response = self.client.get(f'/users/{self.testuser_id}/followers')  # I'm sending a GET request to the followers route.
                self.assertEqual(response.status_code, 200)  # I'm asserting that the response status code is 200, which means the request was successful.

            # I'm defining a test method to test viewing the followers of a user when logged out.
            def test_followers_when_logged_out(self):
                self.logout()  # I'm logging out the user.
                response = self.client.get(f'/users/{self.testuser_id}/followers')  # I'm sending a GET request to the followers route.
                self.assertNotEqual(response.status_code, 200)  # I'm asserting that the response status code is not 200, which means the request was not successful.

            # I'm defining a test method to test adding a message when logged in.
            def test_add_message_when_logged_in(self):
                self.login()  # I'm logging in a user.
                response = self.client.post('/messages/new', data=dict(  # I'm sending a POST request to the "new message" route with the text of the message.
                    text='Hello, World!'
                ), follow_redirects=True)
                self.assertEqual(response.status_code, 200)  # I'm asserting that the response status code is 200, which means the request was successful.
                self.assertIn(b'Hello, World!', response.data)  # I'm asserting that the text of the message is in the response data.

            # I'm defining a test method to test adding a message when logged out.
            def test_add_message_when_logged_out(self):
                self.logout()  # I'm logging out the user.
                response = self.client.post('/messages/new', data=dict(  # I'm sending a POST request to the "new message" route with the text of the message.
                    text='Hello, World!'
                ), follow_redirects=True)
                self.assertNotEqual(response.status_code, 200)  # I'm asserting that the response status code is not 200, which means the request was not successful.

            # I'm defining a test method to test deleting a message when logged in.
            def test_delete_message_when_logged_in(self):
                self.login()  # I'm logging in a user.
                self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)  # I'm adding a message.
                message = Message.query.filter(Message.text == 'Hello, World!').first()  # I'm querying the database for the message.
                response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)  # I'm sending a POST request to the delete message route.
                self.assertEqual(response.status_code, 200)  # I'm asserting that the response status code is 200, which means the request was successful.

    # I'm defining a test method to test deleting a message when logged out.
    def test_delete_message_when_logged_out(self):
        self.login()  # I'm logging in a user.
        self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)  # I'm adding a message.
        db.session.commit()  # I'm committing the session to save the new message to the database.
        self.logout()  # I'm logging out the user.
        message = Message.query.filter(Message.text == 'Hello, World!').first()  # I'm querying the database for the message.
        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)  # I'm sending a POST request to the delete message route.
        self.assertNotEqual(response.status_code, 200)  # I'm asserting that the response status code is not 200, which means the request was not successful.

    # I'm defining a test method to test adding a message as another user.
    def test_add_message_as_another_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id  # I'm setting the current user key in the session to the ID of the test user.

            self.logout()  # I'm logging out the user.

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.another_user_id  # I'm setting the current user key in the session to the ID of another user.

            response = c.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)  # I'm sending a POST request to the "new message" route with the text of the message.

            self.assertEqual(response.status_code, 200)  # I'm asserting that the response status code is 200, which means the request was successful.

            msg = Message.query.one()  # I'm querying the database for the message.
            self.assertEqual(msg.text, 'Hello, World!')  # I'm asserting that the text of the message is "Hello, World!".
            self.assertEqual(msg.user_id, self.another_user_id)  # I'm asserting that the user ID of the message is the ID of another user.

    # I'm defining a test method to test deleting a message as another user.
    def test_delete_message_as_another_user(self):
        self.login()  # I'm logging in a user.
        self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)  # I'm adding a message.
        db.session.commit()  # I'm committing the session to save the new message to the database.
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.another_user_id  # I'm setting the current user key in the session to the ID of another user.
        message = Message.query.filter(Message.text == 'Hello, World!').first()  # I'm querying the database for the message.
        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)  # I'm sending a POST request to the delete message route.
        self.assertNotEqual(response.status_code, 200)  # I'm asserting that the response status code is not 200, which means the request was not successful.

    # I'm defining the main function to run the tests.
    if __name__ == '__main__':
        unittest.main()  # I'm running the tests.