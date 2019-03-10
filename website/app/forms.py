from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    phonenumber = StringField('Phone number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired()])
    phonenumber = StringField('Phone number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    creditcard = StringField('Credit Card Number', validators=[DataRequired()])
    cvv = StringField('CVV Code', validators=[DataRequired()])
    expiration = StringField('Expiration', validators=[DataRequired()])

    submit = SubmitField('Register')

    def validate_number(self, phonenumber):
        user = User.query.filter_by(phonenumber=phonenumber.data).first()
        if user is not None:
            raise ValidationError('That phone number is already registered!')
