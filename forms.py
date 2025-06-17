from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FieldList, FormField, HiddenField, RadioField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
import re # For username validation

# Custom validator for username
def username_validator(form, field):
    if not re.match("^[a-zA-Z0-9_.]*$", field.data):
        raise ValidationError("Username can only contain letters, numbers, underscores, and periods.")
    if ' ' in field.data:
        raise ValidationError("Username cannot contain spaces.")

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), 
                                       Length(min=3, max=25, message="Username must be between 3 and 25 characters."),
                                       username_validator])
    password = PasswordField('Password', 
                             validators=[DataRequired(), 
                                         Length(min=6, message="Password must be at least 6 characters long.")])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), 
                                                 EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class OrganizationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(min=5, max=255)])
    acronym = StringField('Acronym (e.g., SRC)', validators=[DataRequired(), Length(max=50)])
    logo_filename = StringField('Logo Filename (e.g., src_logo.png)', 
                                validators=[DataRequired(), Length(max=255)],
                                description="Ensure the image file exists in 'static/images/organization_logos/'")
    description = TextAreaField('Description (Optional)', validators=[Length(max=500)])
    submit = SubmitField('Save Organization')

class PollForm(FlaskForm):
    title = StringField('Poll Title', validators=[DataRequired(), Length(min=5, max=200)])
    organization = SelectField(
        'Conducting Organization', 
        coerce=int, 
        validators=[DataRequired(message="Please select the organization conducting this poll.")]
    )
    options_data = HiddenField('Options Data')
    submit = SubmitField('Create Poll')


class VoteForm(FlaskForm):
    option = RadioField('Choose an option', validators=[DataRequired(message="Please select an option to vote.")], coerce=int)
    submit = SubmitField('Cast Your Vote')
