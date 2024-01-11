# Import the necessary classes from the flask_wtf module to create forms.
from flask_wtf import FlaskForm

# Import the necessary classes from the wtforms module to create form fields.
from wtforms import StringField, PasswordField, TextAreaField

# Import the necessary classes from the wtforms.validators module to add validation to the form fields.
from wtforms.validators import DataRequired, Email, Length

# Define a form for adding and editing messages.
class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    # Add a text area field for the message text, which is required.
    text = TextAreaField('text', validators=[DataRequired()])

# Define a form for adding users.
class UserAddForm(FlaskForm):
    """Form for adding users."""

    # Add a string field for the username, which is required.
    username = StringField('Username', validators=[DataRequired()])

    # Add a string field for the email, which is required and must be a valid email address.
    email = StringField('E-mail', validators=[DataRequired(), Email()])

    # Add a password field for the password, which must be at least 6 characters long.
    password = PasswordField('Password', validators=[Length(min=6)])

    # Add optional string fields for the image URL, header image URL, bio, and location.
    image_url = StringField('(Optional) Image URL')
    header_image_url = StringField('(Optional) Header Image URL')
    bio = StringField('(Optional) Bio')
    location = StringField('(Optional) Location')

# Define a login form.
class LoginForm(FlaskForm):
    """Login form."""

    # Add a string field for the username, which is required.
    username = StringField('Username', validators=[DataRequired()])

    # Add a password field for the password, which must be at least 6 characters long.
    password = PasswordField('Password', validators=[Length(min=6)])