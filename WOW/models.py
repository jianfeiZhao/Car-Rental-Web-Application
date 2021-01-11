from datetime import datetime
from WOW import db, login_manager, app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(20), unique=False, nullable=False)
    lname = db.Column(db.String(20), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cust_type = db.Column(db.String(20), unique=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg') # profile image
    orders = db.relationship('Orders', backref='cust_name', lazy=True)
    customer = db.relationship('Customer', backref='user', lazy=True)

    def get_reset_token(self, expires_sec=180):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.fname}', '{self.lname}', '{self.cust_type}', '{self.email}')"


class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(20), unique=False, nullable=False)
    lname = db.Column(db.String(20), unique=False, nullable=True)
    cust_str = db.Column(db.String(50), unique=False, nullable=False)
    cust_city = db.Column(db.String(30), unique=False, nullable=False)
    cust_state = db.Column(db.String(20), unique=False, nullable=False)
    cust_zipcode = db.Column(db.Numeric(5), unique=False, nullable=False)
    cust_phone = db.Column(db.Numeric(10), unique=False, nullable=False)
    cust_type = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    services = db.relationship('Service', backref='customer', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': None,
        'polymorphic_on': cust_type }


class Individual(Customer):
    __tablename__ = 'Individual'
    id = db.Column(db.Integer, db.ForeignKey('Customer.id'), primary_key=True)
    dl_no = db.Column(db.Numeric(8), nullable=False)
    insure_cname = db.Column(db.String(30), nullable=False)
    insure_pno = db.Column(db.Numeric(6), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'), nullable=True)
    coupon = db.relationship('Coupon', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity':'Individual',
    }

    def __repr__(self):
        return f"Individual('{self.fname}', '{self.lname}', '{self.cust_type}', '{self.email}',\
            '{self.cust_city}', '{self.dl_no}')"


class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coup_discount = db.Column(db.Numeric(2,2), nullable=False)
    coup_sdate = db.Column(db.Date, nullable=False)
    coup_edate = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"Coupon('{self.id}', '{self.coup_discount}', '{self.coup_sdate}', '{self.coup_edate}')"


class Corporate(Customer):
    __tablename__ = 'Corporate'
    id = db.Column(db.Integer, db.ForeignKey('Customer.id'), primary_key=True)
    emp_id = db.Column(db.Numeric(6), nullable=False)
    corporation_id = db.Column(db.Numeric(4), db.ForeignKey('corporation.id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity':'Corporate',
    }
    
    def __repr__(self):
        return f"Corporate('{self.fname}', '{self.lname}', '{self.cust_type}', '{self.email}',\
            '{self.emp_id}', '{self.corporation_id}')"


class Corporation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.Numeric(8), nullable=False)
    corp_name = db.Column(db.String(30), nullable=False)
    corp_discount = db.Column(db.Numeric(2,2), nullable=False)
    account = db.relationship('Corporate', backref='corporation', lazy=True)

    def __repr__(self):
        return f"Corporation('{self.id}', '{self.corp_name}', '{self.corp_discount}')"


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_fname = db.Column(db.String(20), nullable=False)
    locations = db.Column(db.String(30), nullable=False)
    pickup = db.Column(db.DateTime, nullable=False)
    drop = db.Column(db.DateTime, nullable=False)
    acc_no = db.Column(db.Numeric(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Orders('{self.title}', '{self.date_posted}')"


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(20), nullable=False)
    rental_rate = db.Column(db.Numeric(6,2), nullable=False)
    extra_fee = db.Column(db.Numeric(4,2), nullable=False)
    vehicles = db.relationship('Vehicle', backref='cl', lazy=True)

    def __repr__(self):
        return f"Class('{self.id}', '{self.class_name}', '{self.rental_rate}, '{self.extra_fee}')"


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Numeric(4), nullable=False)
    lpn = db.Column(db.Numeric(6), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('rental_office.id'), nullable=False)
    service = db.relationship('Service', backref='vehicle', lazy=True)

    def __repr__(self):
        return f"Vehicle('{self.id}', '{self.make}', '{self.model}, '{self.year}, '{self.lpn}', '{self.class_id}', '{self.office_id}')"


class Rental_office(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    office_str = db.Column(db.String(30), nullable=False)
    office_city = db.Column(db.String(30), nullable=False)
    office_state = db.Column(db.String(20), nullable=False)
    office_zipcode = db.Column(db.Numeric(5,0), unique=False, nullable=False)
    phone_number = db.Column(db.Numeric(10,0), unique=False, nullable=False)
    vehicles = db.relationship('Vehicle', backref='office', lazy=True)

    def __repr__(self):
        return f"Rental_office('{self.id}', '{self.office_str}', '{self.office_city}', '{self.office_state}', '{self.office_zipcode}')"


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pick_loc_id = db.Column(db.Integer, db.ForeignKey('rental_office.id'), nullable=False)
    drop_loc_id = db.Column(db.Integer, db.ForeignKey('rental_office.id'), nullable=False)
    pick_loc = db.relationship('Rental_office', foreign_keys=[pick_loc_id])
    drop_loc = db.relationship('Rental_office', foreign_keys=[drop_loc_id])
    pick_date = db.Column(db.DateTime, nullable=False)
    drop_date = db.Column(db.DateTime, nullable=False)
    start_odo = db.Column(db.Numeric(10,2), nullable=False)
    end_odo = db.Column(db.Numeric(10,2), nullable=False, default=0)
    day_odo = db.Column(db.Integer, nullable=True)
    vin = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    cust_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    invoice = db.relationship('Invoice', backref='service', lazy=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Service('{self.id}', '{self.pick_loc}', '{self.drop_loc}, '{self.pick_date}, \
            '{self.drop_date}', '{self.start_odo}, '{self.end_odo}, '{self.day_odo}, '{self.vin}', '{self.cust_id}', '{self.date}')"


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invo_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    invo_amount = db.Column(db.Numeric(8,2), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    payment = db.relationship('Payment', backref='invoice', lazy=True)

    def __repr__(self):
        return f"Invoice('{self.id}', '{self.invo_date}', '{self.invo_amount}, '{self.service_id})"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pay_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    card_no = db.Column(db.Numeric(8,0), nullable=False)
    pay_method = db.Column(db.String(10), nullable=False)
    invo_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

    def __repr__(self):
        return f"Payment('{self.id}', '{self.pay_date}', '{self.pay_method}, '{self.invo_id})"
