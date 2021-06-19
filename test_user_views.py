"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, User, Message, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False



class UserVeiwTestClass(TestCase):


    def setUp(self):
        """cleanup all tables befor start tests"""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        db.session.commit()

        self.user = User.signup(username='test_user_1', password='password', email='test_user_1@mail.com', image_url='')
        db.session.commit()

        self.client = app.test_client()


    @classmethod
    def tearDownClass(cls):
        """clean up all tables after tests will complite"""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        db.session.commit()

    def test_singup_user(self):
        """run test to create user account"""

        data = {
            'username': 'test_user_2',
            'password': 'password',
            'email': 'test_user_2@mail.com'
        }

        with self.client as c:
            resp = c.post("/signup", data=data,  follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has username of the current user
            self.assertIn(f'@{data["username"]}', html)

    def test_login_user(self):
        """run test to login user"""

        data = {
            'username': self.user.username,
            'password': 'password'
        }

        with self.client as c:
            resp = c.post("/login", data=data,  follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has username of the current user
            self.assertIn(f'@{self.user.username}', html)

    def test_login_user_invalid_parameters(self):
        """run test to login user with invalid parameters"""

        data = {
            'username': self.user.username,
            'password': 'password_test'
        }

        with self.client as c:
            resp = c.post("/login", data=data,  follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has warning message
            self.assertIn('Invalid credentials.', html)

    def test_to_log_out_user(self):
        """run test to logout user and delete session"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.get('/logout', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui redirected page has logout success message
            self.assertIn('You have been logged out', html)

    def test_show_user_profile(self):
        """run test to show user profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.get(f'/users/{self.user.id}')

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui page has a username of the current user
            self.assertIn(f'@{self.user.username}', html)

    def test_see_following_page(self):
        """when user logged in, try see the follower / following pages for any user"""

        test_user_2 = User(
            email="user_2@test.com",
            username="testuser_2",
            password="password"
        )

        db.session.add(test_user_2)
        db.session.commit()

        self.user.following.append(test_user_2)
        db.session.commit()
        
        username_test_user_2 = test_user_2.username

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.get(f'/users/{self.user.id}/following')

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui page has a username of the following user
            self.assertIn(f'@{username_test_user_2}', html)


    def test_see_following_page_when_logout(self):
        """when user is logged out, is user disallowed from visiting a user’s follower / following pages"""

        test_user_2 = User(
            email="user_2@test.com",
            username="testuser_2",
            password="password"
        )

        db.session.add(test_user_2)
        db.session.commit()

        self.user.following.append(test_user_2)
        db.session.commit()
        
        username_test_user_2 = test_user_2.username

        with self.client as c:

            resp = c.get(f'/users/{username_test_user_2}')

            html = resp.get_data(as_text=True)

            # Make sure it gets 404 because the current user is not loged in
            self.assertEqual(resp.status_code, 404)

    def test_add_message(self):
        """when user is logged in, can user add a message?"""

        message = {'text': 'body test message'}

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.post('/messages/new', data=message, follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has message text
            self.assertIn(message['text'], html)

    def test_delete_message(self):
        """when user is logged in, can user delete a message?"""

        message = Message(text='body test message', user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        message_id = message.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.post(f'/messages/{message_id}/delete', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has 0 messages
            self.assertIn(f'<a href="/users/{self.user.id}">0</a>', html)


    def test_add_message_user_logout(self):
        """when user is logged out, is user prohibited from adding messages?"""

        message = {'text': 'body test message'}

        with self.client as c:

            resp = c.post('/messages/new', data=message, follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has warning message
            self.assertIn('Access unauthorized.', html)

    def test_delete_message_user_logout(self):
        """when user is logged out, is user prohibited from deleting messages?"""

        message = Message(text='body test message', user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        message_id = message.id

        with self.client as c:

            resp = c.post(f'/messages/{message_id}/delete', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has warning message
            self.assertIn('Access unauthorized.', html)

    def test_add_message_as_another_user(self):
        """when user is logged in, is user prohibiting from adding a message as another user?"""

        message = {'text': 'body test message'}

        some_user_id = 3

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = some_user_id

            resp = c.post('/messages/new', data=message, follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has warning message
            self.assertIn('Access unauthorized.', html)

    def test_delete_message_as_another_user(self):
        """when user is logged in, is user prohibiting from deleting a message as another user?"""

        message = Message(text='body test message', user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        message_id = message.id     

        some_user_id = 3
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = some_user_id

            resp = c.post(f'/messages/{message_id}/delete', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            #checking if ui rediracted page has warning message
            self.assertIn('Access unauthorized.', html)



        



