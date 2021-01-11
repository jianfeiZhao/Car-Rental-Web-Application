import secrets, os, sqlite3, time
from PIL import Image
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, abort
from WOW import app, db, bcrypt, mail
from WOW.forms import RegistrationForm, LoginForm, UpdateAccountForm, HomeForm, IndividualForm, \
    CorporateForm, LocationForm, CarsForm, ClassForm, AddLocForm, CorpForm, CoupForm, \
    ServiceForm, EndOrderForm, PaymentForm, RequestResetForm, ResetPasswordForm
from WOW.models import User, Customer, Individual, Corporate, Corporation, Coupon, Vehicle, \
     Class, Rental_office, Service, Invoice, Payment
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


def check_permission(current_user):
    a, b = current_user.email.split('@')
    if a[:5] != 'admin' or b[:3] != 'wow':
        abort(403)
        
###################################### Home Page #########################################

def get_orders(cust_id):
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select id, pick_loc_id, drop_loc_id, pick_date, drop_date, date, end_odo from service \
             where cust_id = " + cust_id + "\
             order by date desc"
        
    rows = cursor.execute(query)
    orders = []
    for row in rows:
        order = []
        for i in range(len(row)):
            order.append(row[i])

        q1 = 'select office_str, office_city, office_state, office_zipcode from rental_office\
            where id=' + str(order[1])
        q2 = 'select office_str, office_city, office_state, office_zipcode from rental_office\
            where id=' + str(order[2])
        cursor = conn.cursor()
        pick_loc = cursor.execute(q1)
        cursor = conn.cursor()
        drop_loc = cursor.execute(q2)
        pick, drop = [], []
        for j in pick_loc:
            pick.append(j)
        for k in drop_loc:
            drop.append(k)
        order[1], order[2] = pick[0], drop[0]
        order[3] = datetime.strptime(order[3][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
        order[4] = datetime.strptime(order[4][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
        order[5] = datetime.strptime(order[5][:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')
        payment = Payment.query.join(Invoice).filter_by(service_id=order[0]).first()
        order.append(payment)
        orders.append(order)
    return orders

@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    form = HomeForm()
    if current_user.is_authenticated:
        a, b = current_user.email.split('@')
        a = a[:5]
        b = b[:3]

        orders = get_orders(str(current_user.id))

        if form.validate_on_submit():
            # validate the pickup and dropoff time
            now = datetime.now()
            if now >= datetime.strptime(str(form.pickup.data), '%Y-%m-%d'):
                flash('The pick-up time cannot be in the past, please adjust your time selection.', 'danger')
                return redirect(url_for('home'))

            if datetime.strptime(str(form.pickup.data), '%Y-%m-%d') >= datetime.strptime(str(form.dropoff.data), '%Y-%m-%d'):
                flash('The drop-off time cannot prior to pick-up time, please adjust your time selection.', 'danger')
                return redirect(url_for('home'))
            
            pick_loc_id = form.pick_loc.data.split(',')[0][1:]
            drop_loc_id = form.drop_loc.data.split(',')[0][1:]
            pick_date = datetime.strftime(form.pickup.data, '%Y-%m-%d')
            drop_date = datetime.strftime(form.dropoff.data, '%Y-%m-%d')
            
            return redirect(url_for('choose_car', pick_loc_id=pick_loc_id, drop_loc_id=drop_loc_id,\
                pick_date=pick_date, drop_date=drop_date))
        
        return render_template('home.html', title='Car Rental', form=form, a=a, b=b, orders=orders)

    elif form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
    return render_template('home.html', title='Car Rental', form=form)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


######################################## Register ###########################################

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(fname=form.fname.data, lname=form.lname.data, email=form.email.data, 
                    cust_type = form.cust_type.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))   # after successfully registered, go back to the login page
    return render_template('register.html', title='Register', form=form)


###################################### Login-Logout #########################################

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


########################################## Account ##########################################

def save_picture(form_picture):
    # save uploaded picture to project file
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    # resize the uploaded picture
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            # check whether profile picture has been updated
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.fname = form.fname.data
        current_user.lname = form.lname.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.fname.data = current_user.fname     # show data on the field
        form.lname.data = current_user.lname 
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/account/individual", methods=['GET', 'POST'])
@login_required
def individual():
    form = IndividualForm()
    customer = Customer.query.get(current_user.id)
    individual = Individual.query.get(current_user.id)
    if customer == None and individual == None:
        if form.validate_on_submit():
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                current_user.image_file = picture_file

            coup = Coupon.query.filter_by(id=form.coupon_no.data).first()

            individual = Individual(id=current_user.id, fname=form.fname.data, lname=form.lname.data, 
                email=form.email.data, cust_type=current_user.cust_type, cust_str=form.cust_str.data, 
                cust_city=form.cust_city.data, cust_state=form.cust_state.data, cust_zipcode=form.cust_zipcode.data, 
                cust_phone=form.cust_phone.data, user=current_user, dl_no=form.dl_no.data, 
                insure_cname=form.insure_cname.data, insure_pno=form.insure_pno.data, coupon=coup)
            db.session.add(individual)
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('account'))
        
        elif request.method == 'GET':
            form.fname.data = current_user.fname     # show data on the field
            form.lname.data = current_user.lname 
            form.email.data = current_user.email
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('individual.html', title='Individual', image_file=image_file, form=form)
    
    else:
        if form.validate_on_submit():
            #coup = Coupon.query.filter_by(coupon_id=form.coupon_no.data).first()
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                current_user.image_file = picture_file
            current_user.fname = form.fname.data
            current_user.lname = form.lname.data
            current_user.email = form.email.data
            customer.cust_str = form.cust_str.data
            customer.cust_city = form.cust_city.data
            customer.cust_phone = form.cust_phone.data
            customer.cust_state = form.cust_state.data
            customer.cust_zipcode = form.cust_zipcode.data
            individual.dl_no = form.dl_no.data
            individual.insure_cname = form.insure_cname.data
            individual.insure_pno = form.insure_pno.data
            individual.coupon_id = form.coupon_no.data
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('account'))

        elif request.method == 'GET':
            form.fname.data = current_user.fname     # show data on the field
            form.lname.data = current_user.lname 
            form.email.data = current_user.email
            form.cust_str.data = customer.cust_str
            form.cust_city.data = customer.cust_city
            form.cust_phone.data = int(customer.cust_phone)
            form.cust_state.data = customer.cust_state
            form.cust_zipcode.data = int(customer.cust_zipcode)
            form.dl_no.data = int(individual.dl_no)
            form.insure_cname.data = individual.insure_cname
            form.insure_pno.data = int(individual.insure_pno)
            form.coupon_no.data = individual.coupon_id

        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('individual.html', title='Individual', image_file=image_file, form=form)


@app.route("/account/corporate", methods=['GET', 'POST'])
@login_required
def corporate():
    form = CorporateForm()
    customer = Customer.query.get(current_user.id)
    corporate = Corporate.query.get(current_user.id)
    if customer == None and corporate == None:
        if form.validate_on_submit():
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                current_user.image_file = picture_file
            
            corp = Corporation.query.filter_by(corp_name=form.corp_name.data).first()

            corporate = Corporate(id=current_user.id, fname=form.fname.data, lname=form.lname.data, 
                email=form.email.data, cust_type=current_user.cust_type, cust_str=form.cust_str.data, 
                cust_city=form.cust_city.data, cust_state=form.cust_state.data, cust_zipcode=form.cust_zipcode.data, 
                cust_phone=form.cust_phone.data, user=current_user, emp_id=form.emp_id.data, 
                corporation_id=corp.id, corporation=corp)
            db.session.add(corporate)
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('account'))
        
        elif request.method == 'GET':
            form.fname.data = current_user.fname     # show data on the field
            form.lname.data = current_user.lname 
            form.email.data = current_user.email
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('corporate.html', title='corporate', image_file=image_file, form=form)
    
    else:
        if form.validate_on_submit():
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                current_user.image_file = picture_file
            corp = Corporation.query.filter_by(corp_name=form.corp_name.data).first()
            current_user.fname = form.fname.data
            current_user.lname = form.lname.data
            current_user.email = form.email.data
            customer.cust_str = form.cust_str.data
            customer.cust_city = form.cust_city.data
            customer.cust_phone = form.cust_phone.data
            customer.cust_state = form.cust_state.data
            customer.cust_zipcode = form.cust_zipcode.data
            corporate.emp_id = form.emp_id.data
            corporate.corporation_id = corp.id
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('account'))

        elif request.method == 'GET':
            corp = Corporation.query.filter_by(id=corporate.corporation_id).first()
            form.fname.data = current_user.fname     # show data on the field
            form.lname.data = current_user.lname 
            form.email.data = current_user.email
            form.cust_str.data = customer.cust_str
            form.cust_city.data = customer.cust_city
            form.cust_phone.data = int(customer.cust_phone)
            form.cust_state.data = customer.cust_state
            form.cust_zipcode.data = int(customer.cust_zipcode)
            form.emp_id.data = int(corporate.emp_id)
            form.corp_name.data = corp.corp_name

        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('corporate.html', title='corporate', image_file=image_file, form=form)


######################################## Get Vehicles ########################################

def get_cars(str):
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from vehicle a\
             join class b on a.class_id = b.id\
             where b.class_name like '%" + str + "'"
    rows = cursor.execute(query)
    cars = []
    for row in rows:
        car = []
        for i in range(len(row)):
            car.append(row[i])
        cars.append(car)
    return cars

@app.route("/vehicles", methods=['GET', 'POST'])
def vehicles():
    cars1 = get_cars('CAR')
    len1 = len(cars1)
    cars2 = get_cars('SUV')
    len2 = len(cars2)
    cars3 = get_cars('VAN')
    len3 = len(cars3)
    cars4 = get_cars('TRUCK')
    len4 = len(cars4)
    return render_template('vehicles.html', title='Vehicles', cars1=cars1, cars2=cars2, cars3=cars3, cars4=cars4,\
            len1=len1, len2=len2, len3=len3, len4=len4)


######################################## Choose Car ########################################

def loc_cars(office_id, c_name):
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from vehicle a\
             join class b on a.class_id = b.id\
             where a.office_id = " + office_id + " and b.class_name like '%" + c_name + "'"
    rows = cursor.execute(query)
    cars = []
    for row in rows:
        car = []
        for i in range(len(row)):
            car.append(row[i])
        cars.append(car)
    return cars

@app.route("/choose-car", methods=['GET', 'POST'])
def choose_car():
    pick_loc_id = request.args.get("pick_loc_id")
    drop_loc_id = request.args.get("drop_loc_id")
    pick_date = request.args.get("pick_date")
    drop_date = request.args.get("drop_date")
    cars1 = loc_cars(pick_loc_id, 'CAR')
    len1 = len(cars1)
    cars2 = loc_cars(pick_loc_id, 'SUV')
    len2 = len(cars2)
    cars3 = loc_cars(pick_loc_id, 'VAN')
    len3 = len(cars3)
    cars4 = loc_cars(pick_loc_id, 'TRUCK')
    len4 = len(cars4)
    return render_template('chooseCar.html', title='Vehicles', cars1=cars1, cars2=cars2, cars3=cars3, \
        cars4=cars4, len1=len1, len2=len2, len3=len3, len4=len4, pick_loc_id=pick_loc_id, \
        drop_loc_id=drop_loc_id, pick_date=pick_date, drop_date=drop_date)


######################################## Find Location ######################################

@app.route("/findlocs", methods=['GET', 'POST'])
def findlocs():
    form = LocationForm()
    if form.validate_on_submit():
        city = form.city.data
        zipcode = form.zipcode.data
        return redirect(url_for('locations', zipcode=zipcode, city=city))
    return render_template('findlocs.html', title='FindLocs', form=form)


def get_loc_cars(office_id):
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query_car = "select a.office_id, a.vin, a.make, a.model, a.year, b.class_name\
                from vehicle a\
                join class b on a.class_id=b.id\
                where a.office_id = " + str(office_id)
    return cursor.execute(query_car)

@app.route("/locations", methods=['GET', 'POST'])
def locations():
    form = LocationForm()
    if form.validate_on_submit():
        city = form.city.data
        zipcode = form.zipcode.data
        return redirect(url_for('locations', zipcode=zipcode, city=city))
    elif request.method == 'GET':
        form.city.data = request.args.get('city')
        form.zipcode.data = request.args.get('zipcode')  

    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    city = request.args.get('city').upper()
    zipcode = request.args.get('zipcode')
    if zipcode == '':
        query = "select * from rental_office \
                 where office_city like '%" + str(city) + "%'"

    else:
        query = "select * from rental_office \
                 where office_city like '%"+str(city)+"%' and office_zipcode = "+zipcode

    rows = cursor.execute(query)
    locations = []
    cars = {}
    for row in rows:
        locations.append(row)
        rows_car = get_loc_cars(row[0])
        cars[row[0]] = []
        for car in rows_car:
            cars[row[0]].append(car)

    num = len(locations)
    return render_template('locations.html', title='Locations', form=form, locations=locations, \
        num=num, cars=cars)


####################################### Update Vehicles #####################################

@app.route("/update-vehicles", methods=['GET', 'POST'])
@login_required
def updateVehicles():
    check_permission(current_user)
    cars1 = get_cars('CAR')
    len1 = len(cars1)
    cars2 = get_cars('SUV')
    len2 = len(cars2)
    cars3 = get_cars('VAN')
    len3 = len(cars3)
    cars4 = get_cars('TRUCK')
    len4 = len(cars4)
    return render_template('updatevehicles.html', title='Update-Vehicles', cars1=cars1, cars2=cars2, cars3=cars3, cars4=cars4,\
            len1=len1, len2=len2, len3=len3, len4=len4)


@app.route("/update-vehicles/new", methods=['GET', 'POST'])
@login_required
def new_car():
    check_permission(current_user)
    form = CarsForm()
    if form.validate_on_submit():
        cl = Class.query.filter_by(class_name=form.class_name.data).first()
        office = Rental_office.query.filter_by(id=form.office_id.data).first()

        car = Vehicle(vin=form.vin.data, make=form.make.data, model=form.model.data, year=form.year.data, \
            lpn=form.lpn.data, class_id=cl.id, office_id=form.office_id.data, cl=cl, office=office)
        db.session.add(car)
        try:
            db.session.commit()
            flash('New car has been added!', 'success')
            return redirect(url_for('updateVehicles'))
        except:
            db.session.rollback()
            flash('Fail to add this car!', 'danger')
            return redirect(url_for('updateVehicles'))
    return render_template('add_car.html', title='New Car', form=form, legend='New Car')


@app.route("/update-vehicles/<int:vehicle_id>/update", methods=['GET', 'POST'])
@login_required
def update_car(vehicle_id):
    check_permission(current_user)
    car = Vehicle.query.get_or_404(vehicle_id)
    form = CarsForm()
    if form.validate_on_submit():
        cl = Class.query.filter_by(class_name=form.class_name.data).first()
        car.vin = form.vin.data
        car.make = form.make.data
        car.model = form.model.data
        car.year = int(form.year.data)
        car.lpn = int(form.lpn.data)
        car.class_id = cl.id
        car.office_id = form.office_id.data
        try:
            db.session.commit()
            flash('The car has been updated!', 'success')
            return redirect(url_for('updateVehicles'))
        except:
            db.session.rollback()
            flash('Fail to update this car!', 'danger')
            return redirect(url_for('updateVehicles'))

    elif request.method == 'GET':      
        cl = Class.query.filter_by(id=car.class_id).first()
        form.vin.data = car.vin
        form.make.data = car.make
        form.model.data = car.model
        form.year.data = int(car.year)
        form.lpn.data = int(car.lpn)
        form.class_name.data = cl.class_name
        form.office_id.data = car.office_id
    return render_template('add_car.html', title='Update Car', form=form, 
                           legend='Update Car')

@app.route("/update-vehicles/<int:vehicle_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_car(vehicle_id):
    check_permission(current_user)
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from vehicle where id="+str(vehicle_id)+";"
    cursor.execute(query)
    try:
        conn.commit()
        flash('The car has been deleted!', 'success')
        return redirect(url_for('updateVehicles'))
    except:
        flash('Fail to delete this car!', 'danger')
        conn.rollback()
        return redirect(url_for('updateVehicles'))


######################################## Update Class #######################################

def get_classes():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from class"
    rows = cursor.execute(query)
    classes = []
    for row in rows:
        cl = []
        for i in range(len(row)):
            cl.append(row[i])
        classes.append(cl)
    return classes

@app.route("/update-class", methods=['GET', 'POST'])
@login_required
def updateClass():
    check_permission(current_user)
    classes = get_classes()
    num = len(classes)
    return render_template('update_class.html', title='Update-Class', classes=classes, num=num)


@app.route("/update-class/<int:class_id>/update", methods=['GET', 'POST'])
@login_required
def update_class(class_id):
    check_permission(current_user)
    cl = Class.query.get_or_404(class_id)
    form = ClassForm()
    if form.validate_on_submit():
        cl.class_name = form.c_name.data.upper()
        cl.rental_rate = form.rental.data
        cl.extra_fee = form.fee.data
        try:
            db.session.commit()
            flash('The class has been updated!', 'success')
            return redirect(url_for('updateClass'))
        except:
            db.session.rollback()
            flash('Fail to update this class!', 'danger')
            return redirect(url_for('updateClass'))

    elif request.method == 'GET':      
        form.c_name.data = cl.class_name
        form.rental.data = cl.rental_rate
        form.fee.data = cl.extra_fee
    return render_template('add_class.html', title='Update Class', form=form, 
                           legend='Update Class')


@app.route("/update-class/<int:class_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_class(class_id):
    check_permission(current_user) 
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from class where id="+str(class_id)+";"
    cursor.execute(query)
    try:
        conn.commit()
        flash('The class has been deleted!', 'success')
        return redirect(url_for('updateClass'))
    except:
        conn.rollback()
        flash('Fail to delete this class!', 'danger')
        return redirect(url_for('updateClass'))


@app.route("/update-class/new", methods=['GET', 'POST'])
@login_required
def new_class():
    check_permission(current_user) 
    form = ClassForm()
    if form.validate_on_submit():
        car = Class(class_name=form.c_name.data.upper(), rental_rate=form.rental.data, extra_fee=form.fee.data)
        db.session.add(car)
        try:
            db.session.commit()
            flash('New class has been added!', 'success')
            return redirect(url_for('updateClass'))
        except:
            db.session.rollback()
            flash('Fail to add this class!', 'danger')
            return redirect(url_for('updateClass'))
    return render_template('add_class.html', title='New Class', form=form, legend='New Class')


##################################### Update Locations ######################################

def get_locations():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from rental_office"
    rows = cursor.execute(query)
    locations = []
    for row in rows:
        location = []
        for i in range(len(row)):
            location.append(row[i])
        locations.append(location)
    return locations

@app.route("/update-locations", methods=['GET', 'POST'])
@login_required
def updateLocation():
    check_permission(current_user) 
    locations = get_locations()
    num = len(locations)
    return render_template('updateLocations.html', title='Locations', locations=locations, num=num)


@app.route("/update-locations/new", methods=['GET', 'POST'])
@login_required
def new_location():
    check_permission(current_user) 
    form = AddLocForm()
    if form.validate_on_submit():
        office = Rental_office(office_str=form.street.data.upper(), office_city=form.city.data.upper(), \
            office_state=form.state.data.upper(), office_zipcode=int(form.zipcode.data), phone_number=int(form.phone.data))
        db.session.add(office)
        try:
            db.session.commit()
            flash('New location has been added!', 'success')
            return redirect(url_for('updateLocation'))
        except:
            db.session.rollback()
            flash('Fail to add this location!', 'danger')
            return redirect(url_for('updateLocation'))
    return render_template('add_loc.html', title='New Location', form=form, legend='New Location')


@app.route("/update-loc/<int:office_id>/update", methods=['GET', 'POST'])
@login_required
def update_location(office_id):
    check_permission(current_user)  
    office = Rental_office.query.get_or_404(office_id)
    form = AddLocForm()
    if form.validate_on_submit():
        office.office_str=form.street.data.upper()
        office.office_city=form.city.data.upper()
        office.office_state=form.state.data.upper()
        office.office_zipcode=int(form.zipcode.data)
        office.phone_number=int(form.phone.data)
        try:
            db.session.commit()
            flash('The location has been updated!', 'success')
            return redirect(url_for('updateLocation'))
        except:
            db.session.rollback()
            flash('Fail to update this location!', 'danger')
            return redirect(url_for('updateLocation'))

    elif request.method == 'GET':      
        form.street.data = office.office_str
        form.city.data = office.office_city
        form.state.data = office.office_state
        form.zipcode.data = int(office.office_zipcode)
        form.phone.data = int(office.phone_number)
    return render_template('add_loc.html', title='Update Location', form=form, 
                           legend='Update Location')


@app.route("/update-location/<int:office_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_location(office_id):
    check_permission(current_user)
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from Rental_office where id="+str(office_id)+";"
    cursor.execute(query)
    try:
       conn.commit()
       flash('The office has been deleted!', 'success')
       return redirect(url_for('updateLocation'))
    except:
        flash('Fail to delete this office!', 'danger')
        conn.rollback()
        return redirect(url_for('updateLocation'))


###################################### Update Corporations ##################################

def get_corporates():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from corporation"
    rows = cursor.execute(query)
    corps = []
    for row in rows:
        corp = []
        for i in range(len(row)):
            corp.append(row[i])
        corps.append(corp)
    return corps

@app.route("/update-corporates", methods=['GET', 'POST'])
@login_required
def updateCorporate():
    check_permission(current_user)
    corps = get_corporates()
    num = len(corps)
    return render_template('updateCorporate.html', title='Corporate', corps=corps, num=num)

@app.route("/update-corporates/new", methods=['GET', 'POST'])
@login_required
def new_corporate():
    check_permission(current_user)
    form = CorpForm()
    if form.validate_on_submit():
        corp = Corporation(reg_no=form.reg_no.data, corp_name=form.corp_name.data.upper(), \
            corp_discount=form.corp_discount.data)
        db.session.add(corp)
        try:
            db.session.commit()
            flash('New corporation has been added!', 'success')
            return redirect(url_for('updateCorporate'))
        except:
            db.session.rollback()
            flash('Fail to add this corporation!', 'danger')
            return redirect(url_for('updateCorporate'))
    return render_template('add_corp.html', title='New Corporation', form=form, legend='New Corporation')


@app.route("/update-corporates/<int:corp_id>/update", methods=['GET', 'POST'])
@login_required
def update_corporate(corp_id):
    check_permission(current_user)
    corp = Corporation.query.get_or_404(corp_id)
    form = CorpForm()
    if form.validate_on_submit():
        corp.reg_no=form.reg_no.data
        corp.corp_name=form.corp_name.data.upper()
        corp.corp_discount=form.corp_discount.data
        try:
            db.session.commit()
            flash('The corporation has been updated!', 'success')
            return redirect(url_for('updateCorporate'))
        except:
            db.session.rollback()
            flash('Fail to update this corporation!', 'danger')
            return redirect(url_for('updateCorporate'))

    elif request.method == 'GET':      
        form.reg_no.data = int(corp.reg_no)
        form.corp_name.data = corp.corp_name
        form.corp_discount.data = corp.corp_discount
    return render_template('add_corp.html', title='Update Corporation', form=form, 
                           legend='Update Corporation')


@app.route("/update-corporates/<int:corp_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_corporate(corp_id):
    check_permission(current_user)
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from Corporation where id="+str(corp_id)+";"
    cursor.execute(query)
    try:
       conn.commit()
       flash('The Corporation has been deleted!', 'success')
       return redirect(url_for('updateCorporate'))
    except:
        flash('Fail to delete this Corporation!', 'danger')
        conn.rollback()
        return redirect(url_for('updateCorporate'))


###################################### Update Coupons ######################################

def get_coupon():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select * from coupon"
    rows = cursor.execute(query)
    coupon = []
    for row in rows:
        coup = []
        for i in range(len(row)):
            coup.append(row[i])
        coupon.append(coup)
    return coupon

@app.route("/update-coupon", methods=['GET', 'POST'])
@login_required
def updateCoupon():
    check_permission(current_user)
    coups = get_coupon()
    num = len(coups)
    return render_template('updateCoupon.html', title='Coupon', coups=coups, num=num)

@app.route("/update-coupon/new", methods=['GET', 'POST'])
@login_required
def new_coupon():
    check_permission(current_user)
    form = CoupForm()
    if form.validate_on_submit():
        coup = Coupon(coup_discount=form.coup_discount.data, coup_sdate=form.coup_sdate.data, \
            coup_edate=form.coup_edate.data)
        db.session.add(coup)
        try:
            db.session.commit()
            flash('New coupon has been added!', 'success')
            return redirect(url_for('updateCoupon'))
        except:
            db.session.rollback()
            flash('Fail to add this coupon!', 'danger')
            return redirect(url_for('updateCoupon'))
    return render_template('add_coup.html', title='New Coupon', form=form, legend='New Coupon')


@app.route("/update-coupon/<int:coup_id>/update", methods=['GET', 'POST'])
@login_required
def update_coupon(coup_id):
    check_permission(current_user)
    coup = Coupon.query.get_or_404(coup_id)
    form = CoupForm()
    if form.validate_on_submit():
        coup.coup_discount=form.coup_discount.data
        coup.coup_sdate=form.coup_sdate.data
        coup.coup_edate=form.coup_edate.data
        try:
            db.session.commit()
            flash('The coupon has been updated!', 'success')
            return redirect(url_for('updateCoupon'))
        except:
            db.session.rollback()
            flash('Fail to update this coupon!', 'danger')
            return redirect(url_for('updateCoupon'))

    elif request.method == 'GET':      
        form.coup_discount.data = coup.coup_discount
        form.coup_sdate.data = coup.coup_sdate
        form.coup_edate.data = coup.coup_edate
    return render_template('add_coup.html', title='Update Coupon', form=form, 
                           legend='Update Coupon')


@app.route("/update-coupon/<int:coup_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_coupon(coup_id):
    check_permission(current_user)
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from Coupon where id="+str(coup_id)+";"
    cursor.execute(query)
    try:
       conn.commit()
       flash('The Coupon has been deleted!', 'success')
       return redirect(url_for('updateCoupon'))
    except:
        flash('Fail to delete this Coupon!', 'danger')
        conn.rollback()
        return redirect(url_for('updateCoupon'))


####################################### Update Customers #####################################

def get_cust():
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "select a.id, b.fname, b.lname, b.email, a.cust_type from user a \
        left outer join customer b on a.id=b.id;"
    rows = cursor.execute(query)
    custs = []
    for row in rows:
        cust = []
        for i in range(len(row)):
            cust.append(row[i])
        custs.append(cust)
    return custs

@app.route("/customers", methods=['GET', 'POST'])
@login_required
def showCustomers():
    check_permission(current_user)
    custs = get_cust()
    num = len(custs)
    return render_template('customers.html', title='Customers', custs=custs, num=num)


@app.route("/update-customer/<int:cust_id>/update", methods=['GET', 'POST'])
@login_required
def update_customer(cust_id):
    check_permission(current_user)
    user = User.query.get_or_404(cust_id)
    if user.cust_type == 'Individual':
        cust = Customer.query.outerjoin(Individual).filter_by(id=cust_id).first()
        form = IndividualForm()
        if form.validate_on_submit():
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                user.image_file = picture_file
            cust.fname=form.fname.data
            cust.lname=form.lname.data
            cust.email=form.email.data
            cust.cust_str=form.cust_str.data
            cust.cust_city=form.cust_city.data
            cust.cust_state=form.cust_state.data
            cust.cust_zipcode=form.cust_zipcode.data
            cust.cust_phone=form.cust_phone.data
            cust.cust_str=form.cust_str.data
            cust.dl_no=form.dl_no.data
            cust.insure_cname=form.insure_cname.data
            cust.insure_pno=form.insure_pno.data
            cust.coupon_id=form.coupon_no.data

            try:
                db.session.commit()
                flash('The customer has been updated!', 'success')
                return redirect(url_for('showCustomers'))
            except:
                db.session.rollback()
                flash('Fail to update this customer!', 'danger')
                return redirect(url_for('showCustomers'))

        elif request.method == 'GET':      
            form.fname.data=cust.fname
            form.lname.data=cust.lname
            form.email.data=cust.email
            form.cust_str.data=cust.cust_str
            form.cust_city.data=cust.cust_city
            form.cust_state.data=cust.cust_state
            form.cust_zipcode.data=int(cust.cust_zipcode)
            form.cust_phone.data=int(cust.cust_phone)
            form.dl_no.data=int(cust.dl_no)
            form.insure_cname.data=cust.insure_cname
            form.insure_pno.data=int(cust.insure_pno)
            form.coupon_no.data=cust.coupon_id

        image_file = url_for('static', filename='profile_pics/' + user.image_file)
        return render_template('individual.html', title='Individual', image_file=image_file, form=form)
    
    elif user.cust_type == 'Corporate':
        cust = Customer.query.outerjoin(Corporate).filter_by(id=cust_id).first()
        form = CorporateForm()
        if form.validate_on_submit():
            if form.picture.data:
                # check whether profile picture has been updated
                picture_file = save_picture(form.picture.data)
                user.image_file = picture_file
            corp = Corporation.query.filter_by(corp_name=form.corp_name.data).first()
            cust.fname = form.fname.data
            cust.lname = form.lname.data
            cust.email = form.email.data
            cust.cust_str = form.cust_str.data
            cust.cust_city = form.cust_city.data
            cust.cust_phone = form.cust_phone.data
            cust.cust_state = form.cust_state.data
            cust.cust_zipcode = form.cust_zipcode.data
            cust.emp_id = form.emp_id.data
            cust.corporation_id = corp.id
            try:
                db.session.commit()
                flash('The customer has been updated!', 'success')
                return redirect(url_for('showCustomers'))
            except:
                db.session.rollback()
                flash('Fail to update this customer!', 'danger')
                return redirect(url_for('showCustomers'))

        elif request.method == 'GET':
            corp = Corporation.query.filter_by(id=cust.corporation_id).first()
            form.fname.data = cust.fname     # show data on the field
            form.lname.data = cust.lname 
            form.email.data = cust.email
            form.cust_str.data = cust.cust_str
            form.cust_city.data = cust.cust_city
            form.cust_phone.data = int(cust.cust_phone)
            form.cust_state.data = cust.cust_state
            form.cust_zipcode.data = int(cust.cust_zipcode)
            form.emp_id.data = int(cust.emp_id)
            form.corp_name.data = corp.corp_name

        image_file = url_for('static', filename='profile_pics/' + user.image_file)
        return render_template('corporate.html', title='corporate', image_file=image_file, form=form)


@app.route("/update-customer/<int:cust_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_customer(cust_id):
    check_permission(current_user)
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = "delete from customer where id="+str(cust_id)+";"
    query1 = "delete from user where id="+str(cust_id)+";"
    cursor.execute(query)
    cursor.execute(query1)
    try:
       conn.commit()
       flash('The customer has been deleted!', 'success')
       return redirect(url_for('showCustomers'))
    except:
        flash('Fail to delete this customer!', 'danger')
        conn.rollback()
        return redirect(url_for('showCustomers'))


###################################### New Service #########################################

@app.route("/service/new", methods=['GET', 'POST'])
@login_required
def new_service():
    car_id = request.args.get("car_id")
    pick_loc_id = request.args.get("pick_loc_id")
    drop_loc_id = request.args.get("drop_loc_id")
    pick_date = request.args.get("pick_date")
    drop_date = request.args.get("drop_date")

    pick_loc = Rental_office.query.filter_by(id=pick_loc_id).first()
    drop_loc = Rental_office.query.filter_by(id=drop_loc_id).first()

    form = ServiceForm()
    if form.validate_on_submit():
        car = Vehicle.query.get_or_404(car_id)
        cust = Customer.query.get_or_404(current_user.id)
        service = Service(pick_loc=pick_loc, drop_loc=drop_loc, pick_date=datetime.strptime(pick_date, '%Y-%m-%d'), \
            drop_date=datetime.strptime(drop_date, '%Y-%m-%d'), start_odo=form.start_odo.data, day_odo=form.daily_odo.data,\
            vehicle=car, customer=cust)
        db.session.add(service)
        try:
            db.session.commit()
            flash('New service has been added!', 'success')
            return redirect(url_for('home'))
        except:
            db.session.rollback()
            flash('Fail to add this service!', 'danger')
            return redirect(url_for('home'))

    elif request.method == 'GET':
        pick_data, drop_data = [], []
        pick_data.append(pick_loc.office_str)
        drop_data.append(drop_loc.office_str)
        pick_data.append(pick_loc.office_city)
        drop_data.append(drop_loc.office_city)
        pick_data.append(pick_loc.office_state)
        drop_data.append(drop_loc.office_state)
        pick_data.append(int(pick_loc.office_zipcode))
        drop_data.append(int(drop_loc.office_zipcode))
        form.pick_loc.data = pick_data
        form.drop_loc.data = drop_data
        form.pickup.data = datetime.strptime(pick_date, '%Y-%m-%d')
        form.dropoff.data = datetime.strptime(drop_date, '%Y-%m-%d')
        car = Vehicle.query.filter_by(id=car_id).first()
        cl = Class.query.filter_by(id=car.class_id).first()
        car_data = {}
        car_data['Class'] = cl.class_name
        car_data['Make'] = car.make
        car_data['Model'] = car.model
        car_data['Rental'] = int(cl.rental_rate)
        car_data['Extra fee'] = int(cl.extra_fee)
        form.car.data = car_data

    return render_template('service.html', title='New Service', form=form, legend='New Service')


def generate_invoice(service, service_id):
    conn = sqlite3.connect('WOW/site.db')
    cursor = conn.cursor()
    query = 'select (julianday(c.drop_date)-julianday(c.pick_date)), c.end_odo-c.start_odo, c.day_odo, \
        d.rental_rate, d.extra_fee from service c \
        join (select * from vehicle a join class b on a.class_id=b.id) d on c.vin=d.id \
        where c.id=' + str(service_id)
    rows = cursor.execute(query)
    result = []
    for row in rows:
        for i in row:
            result.append(i)
    
    show = {}
    show['Number of days you used'] = result[0]
    show['Miles you drived'] =  result[1]
    show['Daily odometer limite'] = result[2]
    show['Rental Rate'] = result[3]
    show['Extra fee'] = result[4]
    print(show)

    # compute the total amount
    if result[2] == '':
        invo_amount = int(result[0])*result[3]
    else:
        if int(result[1]/result[0])-result[2] > 0:
            invo_amount = int(result[0])*result[3] + (round(result[1]/result[0],2)-result[2])*result[4]
        else:
            invo_amount = int(result[0])*result[3]
     
    invoice = Invoice(invo_amount=invo_amount, service=service)
    db.session.add(invoice)
    try:
        db.session.commit()
        flash('Your invoice for this order has been generated, you can pay this order!', 'success')
    except:
        db.session.rollback()
        flash('Fail to generate the invoice for this order!', 'danger')


######################################### End Service ########################################

@app.route("/service/<int:service_id>/end", methods=['GET', 'POST'])
@login_required
def end_order(service_id):
    form = EndOrderForm()
    pick_loc = request.args.get("pick_loc")
    drop_loc = request.args.get("drop_loc")
    pick_date = request.args.get("pick_date")
    drop_date = request.args.get("drop_date")
    service = Service.query.get_or_404(service_id)
   
    # update the vehicle office_id to the return location
    db.session.query(Vehicle).filter(Vehicle.id==service.vin).update({'office_id': service.drop_loc.id})
    db.session.commit()
    flash('Make sure you have returned your car to the return location you chose.', 'warning')
    if form.validate_on_submit():
        # update table
        db.session.query(Service).filter(Service.id==service_id).update({'end_odo': form.end_odo.data})
        try:
            db.session.commit()
            flash('This order has been ended!', 'success')
        except:
            db.session.rollback()
            flash('Fail to end this order!', 'danger')
         
        generate_invoice(service, service_id)

        return redirect(url_for('home'))

    return render_template('endOrder.html', title='End Order', form=form, legend='End This Order', \
        service=service, pick_loc=pick_loc, drop_loc=drop_loc, pick_date=pick_date, drop_date=drop_date)


@app.route("/service/<int:service_id>/pay", methods=['GET', 'POST'])
@login_required
def pay_order(service_id):
    invoice = db.session.query(Invoice).filter(Invoice.service_id==service_id).first()
    service = db.session.query(Service).filter(Service.id==service_id).first()
    if invoice == None:
        service = Service.query.get_or_404(service_id)
        generate_invoice(service, service_id)
        return redirect(url_for('home'))
    form = PaymentForm()
    if form.validate_on_submit():
        payment = Payment(card_no=form.card_no.data, pay_method=form.pay_method.data, invoice=invoice)
        db.session.add(payment)
        try:
            db.session.commit()
            flash('Payment success!', 'success')
            return redirect(url_for('home'))
        except:
            flash('Fail to pay this order!', 'danger')
            return redirect(url_for('home'))

    return render_template('payment.html', title='Payment', form=form, legend='Pay Your Order', \
        invoice=invoice, service=service)


########################################## Payment ############################################

@app.route("/order/<int:order_id>/details", methods=['GET', 'POST'])
@login_required
def order_details(order_id):
    invoice = db.session.query(Invoice).filter(Invoice.id==order_id).first()
    order = Payment.query.filter_by(invo_id=order_id).first()
    
    return render_template('orderDetails.html', invoice=invoice, order=order, legend='Order details')


######################################## Reset password ######################################

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


###################################### Error Page ##########################################

@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500