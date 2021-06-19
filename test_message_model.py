"""Message model tests."""

import os
from unittest import TestCase

from models import db, Message, User, Likes


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app


db.create_all()


class MessageModelTestClass(TestCase):

    def setUp(self):
        """delete all rows from tables"""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        db.session.commit()

        """create user to test inside all methods"""

        self.user = User(
            email="user_1@test.com",
            username="testuser_1",
            password="HASHED_PASSWORD"
        )

        db.session.add(self.user)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        """clean up all tables """

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        db.session.commit()

    def test_create_message_text_body(self):
        """create message body and apply to the user"""

        message = Message(text='message body', user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        #chek if message has same text body as the user
        self.assertEqual(message.text, self.user.messages[0].text)


    def test_check_likes_nmessage(self):
        """check liked message by the user"""

        #create second user
        user = User( email="user_2@test.com", username="testuser_2", password="HASHED_PASSWORD")

        db.session.add(user)
        db.session.commit()

        #apply message to the second user
        message = Message(text='message body', user_id=user.id)

        db.session.add(message)
        db.session.commit()

        #apply like to the message
        like = Likes(user_id=self.user.id, message_id=message.id)

        db.session.add(like)
        db.session.commit()

        #check if user has connected liked message id that inside likes table
        self.assertEqual(like.message_id, user.messages[0].id)

    def test_create_message_invalid_parameters(self):
        """Does create message if any of the validations uniqueness fail"""
        
        #Does fail to create a message when the text body is empty
        message = Message(user_id=self.user.id)

        try: 
            db.session.add(message)
            db.session.commit()
        except:
            db.session.rollback()

        self.assertEqual(self.user.messages, [])


        #Does fail to create a message when the user id is empty
        message = Message(text="body message")

        try: 
            db.session.add(message)
            db.session.commit()
        except:
            db.session.rollback()

        messages = Message.query.all()

        self.assertEqual(messages, [])