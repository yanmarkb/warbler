# Import the necessary modules.
import os
from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import pdb
from flask_migrate import Migrate
from forms import UserAddForm, LoginForm, MessageForm
from models import db, connect_db, User, Message, Likes

# Define a key to get the current user's ID out of the session.
CURR_USER_KEY = "curr_user"

# Create an instance of the Flask class.
# Use __name__, a special built-in Python variable.
# Flask uses it to know where to look for other files such as templates.
app = Flask(__name__)

# Set configuration variables on the Flask app.
# Get these values from the OS environment variables (useful in production)
# or use a default value.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Initialize the DebugToolbarExtension with the app.
toolbar = DebugToolbarExtension(app)

# Call the connect_db function and pass in the app.
# This function sets up the connection to the database.
connect_db(app)

# Create an instance of the Migrate class.
# This connects the app and the db and allows running migrations.
migrate = Migrate(app, db)

# Use this decorator to make this function run before every request.
# Check if the current user's ID is in the session.
# If it is, get that user from the database and set it on g.user.
# If it's not, set g.user to None.
@app.before_request
def add_user_to_g():
    """If a user is logged in, add the current user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

# This function logs in a user.
# It does this by adding the user's ID to the session.
def do_login(user):
    """Log in a user."""
    session[CURR_USER_KEY] = user.id

# This function logs out a user.
# It does this by deleting the user's ID from the session.
def do_logout():
    """Logout a user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

# This is a route for signing up a user.
# If the form validates, I try to create the user and add them to the database.
# If the username is already taken, I flash a message and re-render the form.
# If the form doesn't validate, I just render the form.
@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""
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

# This is a route for logging in a user.
# If the form validates, I try to authenticate the user.
# If the user is authenticated, I log them in and redirect them to the homepage.
# If the user isn't authenticated, I flash a message and re-render the form.
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

# This is a route for logging out a user.
# Calls the logout method on the User model, flashes a success message, and then redirects to the homepage.
@app.route('/logout')
def logout():
    """Handle logout of user."""
    User.logout()
    flash("You have successfully logged out. See you later!", "success")
    return redirect('/')

# This is a route for listing all users.
# If a 'q' parameter is provided in the query string, filters the users by that username.
# Then renders a template with the list of users.
@app.route('/users')
def list_users():
    """Page with listing of users."""
    search = request.args.get('q')
    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()
    return render_template('users/index.html', users=users)

# This is a route for showing a user's profile.
# Gets the user by their ID and gets their messages.
# Then renders a template with the user and their messages.
@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/", 403)
    user = User.query.get_or_404(user_id)
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)

# This is a route for showing who a user is following.
# Gets the user by their ID and then renders a template with the user.
@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)

# This is a route for showing a user's followers.
# Gets the user by their ID and then renders a template with the user.
@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)

# This is a route for adding a follow for the currently logged in user.
# Gets the user to be followed by their ID, adds them to the current user's following list, and then commits the session.
# Then redirects to the page showing who the current user is following.
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

# This is a route for having the currently logged in user stop following another user.
# Gets the user to be unfollowed by their ID, removes them from the current user's following list, and then commits the session.
# Then redirects to the page showing who the current user is following.
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

# This is a route for updating the profile of the current user.
# If the user is not logged in, flashes an error message and redirects to the homepage.
# Gets the current user from the database and creates a form with their data.
# If the form validates, authenticates the user with their current username and the password from the form.
# If the user is authenticated, updates their data and commits the session.
# Then redirects to the user's profile page.
# If the user is not authenticated, flashes an error message.
# Then renders the form.
@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(g.user.id)
    form = UserAddForm(obj=user)
    num_liked_messages = len(user.likes)
    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or user.image_url
            user.header_image_url = form.header_image_url.data or user.header_image_url
            user.bio = form.bio.data
            user.location = form.location.data
            db.session.commit()
            return redirect(f"/users/{user.id}")
        else:
            flash("Invalid password, please try again.", "danger")
    return render_template("users/edit.html", form=form, user=user, num_liked_messages=num_liked_messages)

# This is a route for deleting a user.
# If the user is not logged in, flash an error message and redirect to the homepage.
# Log out the user, delete them from the database, and commit the session.
# Then redirect to the signup page.
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

# This is a route for adding a message.
# If the user is not logged in, flash an error message and redirect to the homepage.
# Get the user from the session and the database.
# If the user doesn't exist, flash an error message and redirect to the homepage.
# Create a form for the message.
# If the form validates, create a new message with the text from the form, add it to the user's messages, and commit the session.
# Then redirect to the user's profile page.
# Render the form.
@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:
    Show form if GET. If valid, update message and redirect to user page.
    """
    if CURR_USER_KEY not in session:
        flash("Access unauthorized.", "danger")
        return redirect("/", code=401)
    user_id = session[CURR_USER_KEY]
    user = User.query.get(user_id)
    if not user:
        flash("Access unauthorized.", "danger")
        return redirect("/", code=401)
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        user.messages.append(msg)
        db.session.commit()
        return redirect(f"/users/{user.id}")
    return render_template('messages/new.html', form=form)

# This is a route for showing a message.
# Get the message by its ID and render it in a template.
@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""
    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)

# This is a route for deleting a message.
# If the user is not logged in, flash an error message and redirect to the homepage.
# Get the message by its ID.
# If the message's user ID is not the same as the current user's ID, flash an error message and redirect to the homepage.
# Delete the message from the database and commit the session.
# Then redirect to the user's profile page.
@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/", 403)
    msg = Message.query.get(message_id)
    if msg.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/", 403)
    db.session.delete(msg)
    db.session.commit()
    return redirect(f"/users/{g.user.id}")

# This is a route for the homepage.
# If the user is logged in, get the IDs of the users they are following and their own ID.
# Then get the 100 most recent messages from those users and render them in a template.
# If the user is not logged in, render a different template.
@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    
    if g.user:
        following_ids = [u.id for u in g.user.following]
        following_ids.append(g.user.id)
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')

# This is a route for toggling a like for a message for the current user.
# If the user is not logged in, flash an error message and redirect to the homepage.
# Get the message by its ID.
# Check if the user has already liked the message.
# If they have, remove the like.
# If they haven't, add a new like.
# Commit the session and redirect to the referrer URL or the homepage if the referrer URL is not set.
@app.route('/users/toggle_like/<int:msg_id>', methods=['POST'])
def toggle_like(msg_id):
    """Toggle a liked message for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(msg_id)

    like = Likes.query.filter_by(user_id=g.user.id, message_id=message.id).first()

    if like:
        # If the user has already liked the message, remove the like
        db.session.delete(like)
    else:
        # If the user hasn't liked the message, add a new like
        new_like = Likes(user_id=g.user.id, message_id=message.id)
        db.session.add(new_like)

    db.session.commit()

    # Redirect to the referrer URL if it's set, otherwise redirect to the home page
    return redirect(request.referrer or url_for('homepage'))
    
# This is a route for showing the messages a user has liked.
# If the user is not logged in, flash an error message and redirect to the homepage.
# Get the user by their ID and their liked messages.
# Render a template with the user and their liked messages.
@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show list of liked messages for a user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    messages = user.likes
    return render_template('users/likes.html', user=user, messages=messages)

# This is a function that is run after every request.
# It adds headers to the response that prevent caching.
@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req