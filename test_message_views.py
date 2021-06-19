"""Message View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        """clean up all tables """

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"},  follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

            #checking if ui rediracted page has username of the current user
            self.assertIn(f'@{self.testuser.username}', html)


    def test_add_like_to_message(self):
        """test to add like to the message"""

        user = User(username="new_user", email="new_user@mail.com", password="password")

        db.session.add(user)
        db.session.commit()

        message = Message(text="body message", user_id=user.id)

        db.session.add(message)
        db.session.commit()
        
        id = message.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/add_like/{id}", follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            # check if user page has a liked message
            resp = c.get(f'/users/{self.testuser.id}')

            likes = Likes.query.filter_by(user_id=self.testuser.id).all()

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(likes), 1)

            #make sure that the ui shows the same amout liked messages as a database has
            self.assertIn(f'<a href="/users/{self.testuser.id}/likes">{len(likes)}</a>', html)


    def test_remove_like_from_message(self):
        """test to remove like from the message"""

        user = User(username="new_user", email="new_user@mail.com", password="password")

        db.session.add(user)
        db.session.commit()

        message = Message(text="body message", user_id=user.id)

        db.session.add(message)
        db.session.commit()
        
        id = message.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            #add like to the message
            resp = c.post(f"/users/add_like/{id}", follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #remove like from the message
            resp = c.post(f"/users/add_like/{id}", follow_redirects=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            # check if user page does not have liked messages
            resp = c.get(f'/users/{self.testuser.id}')

            likes = Likes.query.filter_by(user_id=self.testuser.id).all()

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(likes), 0)

            #make sure that the ui shows the same amout liked messages as a database has
            self.assertIn(f'<a href="/users/{self.testuser.id}/likes">{len(likes)}</a>', html)


    def test_to_delete_message(self):
        """test to delete message"""

        message = Message(text="body message", user_id=self.testuser.id)

        db.session.add(message)
        db.session.commit()

        id = message.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id


            resp = c.post(f"/messages/{id}/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)

            #try to get all message are related to the user
            messages = Message.query.filter_by(user_id=self.testuser.id).all()

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #make sure that the ui shows the same amout user's messages as a database has
            self.assertIn(f'<a href="/users/{self.testuser.id}">{len(messages)}</a>', html)
    



