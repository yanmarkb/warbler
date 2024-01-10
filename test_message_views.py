"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all() 
        db.create_all()  

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser", email="test@test.com", password="testpassword", image_url=None)
        self.another_user = User.signup(username="anotheruser", email="another@test.com", password="anotherpassword", image_url=None)

        db.session.commit()

        self.testuser_id = self.testuser.id
        self.another_user_id = self.another_user.id

    def tearDown(self):
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

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
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

    def test_followers_when_logged_in(self):
        self.login()
        response = self.client.get(f'/users/{self.testuser_id}/followers') 
        self.assertEqual(response.status_code, 200)

    def test_followers_when_logged_out(self):
        self.logout()
        response = self.client.get(f'/users/{self.testuser_id}/followers')
        self.assertNotEqual(response.status_code, 200)

    def test_add_message_when_logged_in(self):
        self.login()

        response = self.client.post('/messages/new', data=dict(
            text='Hello, World!'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, World!', response.data)

    def test_add_message_when_logged_out(self):
        self.logout()
        response = self.client.post('/messages/new', data=dict(
            text='Hello, World!'
        ), follow_redirects=True)
        self.assertNotEqual(response.status_code, 200)

    def test_delete_message_when_logged_in(self):
        self.login()
        self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)
        message = Message.query.filter(Message.text == 'Hello, World!').first()
        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_delete_message_when_logged_out(self):
        self.login()
        self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)
        db.session.commit() 
        self.logout()
        message = Message.query.filter(Message.text == 'Hello, World!').first()
        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)
        self.assertNotEqual(response.status_code, 200)

    def test_add_message_as_another_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            self.logout()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.another_user_id

            response = c.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)

            self.assertEqual(response.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, 'Hello, World!')
            self.assertEqual(msg.user_id, self.another_user_id)

    def test_delete_message_as_another_user(self):
        self.login()
        self.client.post('/messages/new', data=dict(text='Hello, World!'), follow_redirects=True)
        db.session.commit() 
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.another_user_id  
        message = Message.query.filter(Message.text == 'Hello, World!').first()
        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects=True)
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()