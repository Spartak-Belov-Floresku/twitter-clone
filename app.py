import os

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)



##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def get_all_likes():
    """get all messaget that were liked by the user"""

    return Likes.query.filter_by(user_id=g.user.id).all()


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have been logged out", 'danger')

    return redirect("/login")


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())

    return render_template('users/show.html', user=user, messages=messages, likes=get_all_likes())


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, likes=get_all_likes())


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, likes=get_all_likes())


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/api/add_like/message', methods=['PATCH'])
def add_like_to_message():
    """add like to the message using api"""

    #getting data from ui side
    json_data = request.json.get('$json')
    user_id = json_data.get('session_id')
    id_message = int(json_data.get('message_id'))

    user = User.query.get_or_404(user_id)

    if not user:
        return jsonify(resp=False)

    #check if the message already was liked by the current user. If it is, to unliked it
    likes = Likes.query.filter_by(user_id=g.user.id).all()
    likes_id = []

    if likes:
        likes_id = [like.message_id for like in likes]
        if id_message in likes_id:
            Likes.query.filter_by(message_id=id_message).delete()
            db.session.commit()
            
            return jsonify(resp=False)

    #create a new like obj related to the user and the message
    like = Likes(user_id = g.user.id, message_id = id_message)
    db.session.add(like)
    db.session.commit()

    return jsonify(resp=True)


@app.route('/users/<int:user_id>/likes')
def show_page_liked_messages(user_id):
    """show user page with liked messages"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    likes = Likes.query.filter_by(user_id=user_id).all()
    likes_id = []
    messages = []

    
    if likes:
        #extract all message's ids that were liked
        likes_id = [like.message_id for like in likes]

        #extract all messages that were liked
        messages = [Message.query.get(message_id) for message_id in likes_id]

    return render_template('home.html', messages=messages, likes=likes_id)



@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = EditUserForm(obj=g.user)

    if form.validate_on_submit():
        #updated user data
        password = form.password.data

        #check if user typed a correct password
        user = User.authenticate(g.user.username, form.password.data)
        if user:
            
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            user.header_image_url = form.header_image_url.data
            user.bio = form.bio.data
            db.session.commit()

            return redirect(f"/users/{user.id}")
        
        else:

            flash("Access unauthorized.", "danger")
            return redirect("/")

    form.password.data = ''
    return render_template('users/edit.html', form=form)
    


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/api/messages/new', methods=["POST"])
def messages_add_api():
    """Add a message using api route"""

    """getting data for the message"""

    #getting data from ui side
    json_data = request.json.get('$json')
    user_id = json_data.get('session_id')
    message = json_data.get('message')

    user = User.query.get_or_404(user_id)

    if not user:
        return jsonify(resp=False)

    msg = Message(text=message)
    user.messages.append(msg)
    db.session.commit()

    return jsonify(resp=True)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        
        #get all following users and their ids
        users_following = g.user.following
        ids = [user.id for user in users_following]

        #get all likes messages by the user
        likes = Likes.query.filter_by(user_id=g.user.id).all()
        likes_id = []
        if likes:
            likes_id = [like.message_id for like in likes]


        #get all following users's messages
        messages = (Message.query.filter(Message.user_id.in_(ids)).order_by(Message.timestamp.desc()).limit(100).all())

        return render_template('home.html', messages=messages, likes=likes_id)

    else:
        return render_template('home-anon.html')

##############################################################################
#enable 404 page to handle incorrect requests


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
