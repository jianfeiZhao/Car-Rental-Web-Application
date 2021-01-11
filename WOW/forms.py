from flask_wtf import FlaskForm
import sqlite3, datetime
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DateField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError   # validate the input data
from WOW.models import User, Corporation, Class, Vehicle#, Coupon

# User Registration
class RegistrationForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    cust_type = SelectField('Customer Type', validators=[DataRequired()], choices=['Individual', 'Corporate'])
    password = PasswordField('Password(At least 6 characters)', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Your already have an account, login directly.')

# Extra info
class IndividualForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    cust_str = StringField('Street', validators=[DataRequired()])
    cust_city = StringField('City', validators=[DataRequired()])
    cust_state = StringField('State', validators=[DataRequired()])
    cust_zipcode = StringField('Zipcode', validators=[DataRequired(), Length(min=5, max=5)])
    cust_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    dl_no = StringField('Driver License Number', validators=[DataRequired()])
    insure_cname = StringField('Insurance Company Name', validators=[DataRequired()])
    insure_pno = StringField('Insurance Policy Number', validators=[DataRequired()])
    coupon_no = StringField('Coupon Number')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        a, b = current_user.email.split('@')
        a = a[:5]
        b = b[:3]
        if email.data != current_user.email: 
            if a != 'admin' and b != 'wow':
                user = User.query.filter_by(email=email.data).first()
                if user:
                    raise ValidationError('That email is taken. Please choose another one.')

def get_corp_choices():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select distinct corp_name from Corporation"
    rows = cursor.execute(query)
    choices = []
    for row in rows:
        for i in row:
            choices.append(i)
    return choices

class CorporateForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    cust_str = StringField('Street', validators=[DataRequired()])
    cust_city = StringField('City', validators=[DataRequired()])
    cust_state = StringField('State', validators=[DataRequired()])
    cust_zipcode = StringField('Zipcode', validators=[DataRequired(), Length(min=5, max=5)])
    cust_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    corp_name = SelectField('Company Name', validators=[DataRequired()], choices=get_corp_choices())
    emp_id = StringField('Employee ID', validators=[DataRequired()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        a, b = current_user.email.split('@')
        a = a[:5]
        b = b[:3]
        if email.data != current_user.email: 
            if a != 'admin' and b != 'wow':
                user = User.query.filter_by(email=email.data).first()
                if user:
                    raise ValidationError('That email is taken. Please choose another one.')

# User Login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    cust_type = SelectField('Customer Type', validators=[DataRequired()], choices=['Individual', 'Corporate'])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    # make sure the username is not empty and between 2 and 20 characters
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose another one.')

def get_locs():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select id, office_str, office_city, office_state, office_zipcode from rental_office;"
    rows = cursor.execute(query)
    choices = []
    for row in rows:
        choices.append(str(row))
    return choices

class HomeForm(FlaskForm):
    pick_loc = SelectField('Pickup Location', validators=[DataRequired()], choices=get_locs())
    drop_loc = SelectField('Return Location', validators=[DataRequired()], choices=get_locs())
    pickup = DateField('Pickup Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    dropoff = DateField('Return Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    submit = SubmitField('Next')


class LocationForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    zipcode = StringField('Zipcode', validators=[Length(max=5)])
    submit = SubmitField('Submit')

def get_choices1():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select distinct class_name from class"
    rows = cursor.execute(query)
    choices = []
    for row in rows:
        for i in row:
            choices.append(i)
    return choices

def get_choices2():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select id from rental_office"
    rows = cursor.execute(query)
    choices = []
    for row in rows:
        for i in row:
            choices.append(i)
    return choices

class CarsForm(FlaskForm):
    vin = StringField('Vehicle Identification Number', validators=[DataRequired()])
    make = StringField('Make', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    lpn = StringField('License Plate Number', validators=[DataRequired()])
    class_name = SelectField('Class Name', validators=[DataRequired()], choices=get_choices1())
    office_id = SelectField('Office Number', validators=[DataRequired()], choices=get_choices2())
    submit = SubmitField('Submit')

class ClassForm(FlaskForm):
    c_name = StringField('Class Name', validators=[DataRequired()])
    rental = StringField('Rental Rate per day', validators=[DataRequired()])
    fee = StringField('Over mileage fee', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddLocForm(FlaskForm):
    street = StringField('Street', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=10)])
    zipcode = StringField('Zipcode', validators=[Length(max=5)])
    submit = SubmitField('Submit')

class CorpForm(FlaskForm):
    reg_no = StringField('Register Number', validators=[DataRequired()])
    corp_name = StringField('Corporation Name', validators=[DataRequired()])
    corp_discount = StringField('Corporation discount', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CoupForm(FlaskForm):
    coup_discount = StringField('Discount', validators=[DataRequired()])
    coup_sdate = DateField('Start Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    coup_edate = DateField('End Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    submit = SubmitField('Submit')

class ServiceForm(FlaskForm):
    pick_loc = StringField('Pickup Location', validators=[DataRequired()])
    drop_loc = StringField('Return Location', validators=[DataRequired()])
    pickup = DateField('Pickup Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    dropoff = DateField('Return Date', validators=[DataRequired()], format="%m-%d-%Y", render_kw={'placeholder': 'mm-dd-yyyy'})
    car = TextAreaField('Vehicle Info', validators=[DataRequired()])
    start_odo = StringField('Start Odometer', validators=[DataRequired()])
    daily_odo = StringField('Daily Odometer Limite', render_kw={'placeholder': 'Could be None'})
    submit = SubmitField('Next')

class EndOrderForm(FlaskForm):
    end_odo = StringField('End Odometer', validators=[DataRequired()])
    submit = SubmitField('Submit')

class PaymentForm(FlaskForm):
    pay_method = SelectField('Payment Method', validators=[DataRequired()], choices=['Credit Card','Debit Card','Gift Card'])
    card_no = StringField('Card Number', validators=[DataRequired()])
    submit = SubmitField('Pay Now')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')