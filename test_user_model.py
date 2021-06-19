"""User model tests."""

import os
from unittest import TestCase

from models import db, User, Follows


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app


db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """delete all rows from tables"""

        User.query.delete()
        Follows.query.delete()

        db.session.commit()

        """create user_1 and user_2 to test inside all methods"""

        self.user_1 = User(
            email="user_1@test.com",
            username="testuser_1",
            password="HASHED_PASSWORD"
        )

        # second user is created with hashed password
        self.user_2 = User.signup(
            username="testuser_2", 
            email="user_2@test.com", 
            password="test_password_2",
            image_url= "empty"
        )

        db.session.add_all([self.user_1, self.user_2])
        db.session.commit()


    @classmethod
    def tearDownClass(cls):
        """clean up all tables """

        User.query.delete()
        Follows.query.delete()

        db.session.commit()
        

    def test_user_model(self):
        """Does basic model work?"""
        # users should have no messages & no followers
        self.assertEqual(len(self.user_1.messages), 0)
        self.assertEqual(len(self.user_1.followers), 0)
        self.assertEqual(len(self.user_2.messages), 0)
        self.assertEqual(len(self.user_2.followers), 0)


    def test_user_is_following_model(self):
        """Does successfully detect when user_1 is following user_2"""

        self.user_1.following.append(self.user_2)
        db.session.commit()

        #request data from follows table
        follow = Follows.query.filter_by(user_following_id  = self.user_1.id).first()

        self.assertEqual(follow.user_being_followed_id , self.user_2.id)

        #self.user_1 should have one following

        self.user_1.following.remove(self.user_2)
        db.session.commit()

        #request data from follows table
        follow = Follows.query.filter_by(user_following_id  = self.user_1.id).first()

        #self.user_1 should have no following
        self.assertEqual(follow, None)


    def test_user_is_followed_by_another_user_model(self):
        """Does successfully detect when user_1 is followed by user_2"""

        self.user_1.followers.append(self.user_2)
        db.session.commit()

        #request data from follows table
        follow = Follows.query.filter_by(user_being_followed_id  = self.user_1.id).first()

        self.assertEqual(follow.user_following_id  , self.user_2.id)


        #self.user_1 should have one followers
        self.user_1.followers.remove(self.user_2)
        db.session.commit()

        #request data from follows table
        follow = Follows.query.filter_by(user_being_followed_id  = self.user_1.id).first()

        #self.user_1 should have no followers
        self.assertEqual(follow, None)

    def test_to_create_new_user_model(self):
        """Does successfully create a new user given valid credentials"""

        new_user = self.user_1 = User(
            email="user_3@test.com",
            username="testuser_3",
            password="HASHED_PASSWORD"
        )

        db.session.add(new_user)
        db.session.commit()

        #check if new user has been successfully created
        user_3 = User.query.get(new_user.id)

        self.assertEqual(user_3.username, "testuser_3")

    def test_to_create_new_user_same_email_model(self):
        """Does fail to create a new user if any of the validations uniqueness fail"""

        user_3 = User(
            email="user_1@test.com",
            username="testuser_3",
            password="HASHED_PASSWORD"
        )

        try: 
            db.session.add(user_3)
            db.session.commit()
        except:
            db.session.rollback()

        user_3 = User.query.filter(User.username == 'testuser_3').first()

        # check that result returns None
        self.assertEqual(user_3, None)


    def test_to_athenticate_user(self):
        """athentication test for user"""

        #Does successfully return a user when given a valid username and password
        user = User.authenticate(username = self.user_2.username, password = 'test_password_2')

        self.assertEqual(user.username, self.user_2.username)


        #Does fail to return a user when the username is invalid
        user = User.authenticate(username = 'testuser_3', password = 'test_password')

        self.assertEqual(user, False)

        #Does fail to return a user when the password is invalid
        user = User.authenticate(username = self.user_2.username, password = 'test_password_3')

        self.assertEqual(user, False)

    