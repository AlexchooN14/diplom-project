from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     TextAreaField, SelectField, IntegerRangeField, FloatField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from pocketparadise.models import User, City, Country
from flask_login import current_user


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(max=30)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=15)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), Length(min=6, max=15), EqualTo('password')])
    # city = StringField('City of living', validators=[DataRequired(), Length(max=45)])
    country = SelectField('Country of living', choices=[('BG', 'Bulgaria'), ('FR', 'France')])
    city = SelectField('City of living', choices=[])
    # country = StringField('Country of living', validators=[DataRequired(), Length(max=45)])
    submit = SubmitField('Sign up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already used. Choose a different one')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=15)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log In')


class UpdateAccountForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(max=30)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_email(self, email):
        user_same_email = User.query.filter_by(email=email.data).first()
        if user_same_email and user_same_email != current_user:
            raise ValidationError('Email is already used. Choose a different one')


class ZoneForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=40)])
    watering_amount = IntegerRangeField('Irrigation amount per sq.m. per 24h')  # TODO check if that works
    source_flowrate = FloatField('Flow rate of water source', validators=[DataRequired()])
    area_size = FloatField('Physical area of zone in sq.m.', validators=[DataRequired()])
    algorithm = SelectField('Algorithm mode', choices=[('MOST', 'Highest Moisture - Trees, Vegetables'),
                                                       ('MEDIUM', 'Medium Moisture - Flowers, Grass'),
                                                       ('LEAST', 'Least Moisture - Small plants, Pots')])
    submit = SubmitField('Post')

