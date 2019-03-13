from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phonenumber=form.phonenumber.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, phonenumber=form.phonenumber.data, creditcard=form.creditcard.data, cvv=form.cvv.data, expiration=form.expiration.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


import smartcar
import datetime
from flask import Flask, request, redirect, jsonify
from twilio.twiml.messaging_response import MessagingResponse
#from flask_cors import CORS
from math import sin, cos, sqrt, atan2, radians

from app import app, db
from app.models import User, Trip


#app = Flask(__name__)
#CORS(app)

access = None
#user's location--hard-coded to Rutgers Student Center for now
userlat = 40.5055
userlong = -74.45188903808594

client = smartcar.AuthClient(
    client_id='906e6fc9-ee9e-4622-b19c-6055e4a7afe0',
    client_secret='uWu',
    redirect_uri='http://localhost:5000/exchange',
    scope=['read_vehicle_info', 'read_location', 'read_odometer', 'control_security', 'control_security:unlock', 'control_security:lock'],
    #test_mode=True
)


@app.route('/auth', methods=['GET'])
def auth():
    auth_url = client.get_auth_url()
    return redirect(auth_url)


@app.route('/exchange', methods=['GET'])
def exchange():
    code = request.args.get('code')
    print("\n\nhere's the code:\n")
    print(code)

    global access
    # in a production app you'll want to store this in some kind of
    # persistent storage
    access = client.exchange_code(code)
    return '', 200


cars = []
carsinfo = []
carconfirmed = 0
myrental = None
startingmileage = 0
priceperkm = 0.20
startlat = 0
startlon = 0

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    text = request.values.get('Body', None)
    print("Number from: ")
    print(str(request.values.get('From', None)))

    resp = MessagingResponse()

    global cars
    global carsinfo
    global carconfirmed
    global myrental
    global startingmileage
    global priceperkm
    global startlat
    global startlon

    if carconfirmed == 0 and "rent" in text.lower() and "car" in text.lower():
        cars = []
        carsinfo = []
        global access
        vehicle_ids = smartcar.get_vehicle_ids(access['access_token'])['vehicles']
        for v in vehicle_ids:
            c = 1
            vehicle = smartcar.Vehicle(v, access['access_token'])
            dist = calc_distance(userlat, userlong, vehicle.location()["data"]["latitude"], vehicle.location()["data"]["longitude"])
            print("location: \n")
            print(vehicle.location())
            print("Distance: \n\n")
            print(dist)
            if dist < 15:
                cars.append(vehicle)
                vinfo = vehicle.info()
                info = "Car " + str(c) + ": " + str(vinfo["year"])  + " " + str(vinfo["make"]) + " " + str(vinfo["model"])
                info += ", " + str(dist)[0:4] + " km away"
                carsinfo.append(info)
            c += 1

        response = "Ok, here are all the rental cars available within a 15-km radius:\n"
        for s in carsinfo:
            response += s + "\n"
        response += "\nTo see more about a car, respond with 'Car <number>'"
        resp.message(response)
    elif carconfirmed == 0 and "car" in text.lower():
        carnum = int(text.replace("Car ", ""))
        print("Carnum = " + str(carnum))
        print("len(cars) = " + str(len(carsinfo)))
        if carnum > len(cars):
            resp.message("That's not a valid Car number!")
        else:
            vehicle = cars[carnum-1]
            response = "Ok, here's some information about Car " + str(carnum) + ":\n"
            vinfo = vehicle.info()
            response += str(vinfo["year"])  + " " + str(vinfo["make"]) + " " + str(vinfo["model"]) + "\n"
            vodom = vehicle.odometer()
            response += "Mileage: " + str(int(vodom["data"]["distance"])) + " km\n"
            response += "Pricing: $" + str(priceperkm)[0:4] + "/km\n"
            vloc = vehicle.location()
            startlat = vloc["data"]["latitude"]
            startlon = vloc["data"]["longitude"]
            response += "Location: https://www.google.com/maps/place/" + str(vloc["data"]["latitude"]) + "+" + str(vloc["data"]["longitude"]) + "/ \n\n"
            response += "To confirm this car rental, respond with 'Confirm'\n(note that confirming will unlock the car)"
            resp.message(response)
            myrental = vehicle
            carconfirmed = 1
    elif carconfirmed == 1 and "confirm" in text.lower():
    #    myrental.unlock()
        startingmileage = myrental.odometer()["data"]["distance"]
        response = "Ok, your rental has been confirmed! Your rental car has been unlocked.\nRespond with 'Done' when you are finished."
        resp.message(response)
    elif carconfirmed == 1 and "Done" in text:
    #    myrental.lock()
        distancetravelled = myrental.odometer()["data"]["distance"] - startingmileage
        print("distancetravelled:\n")
        print(distancetravelled)
        response = "Ok, your rental has been locked!\nTotal distance travelled: " + str(int(distancetravelled)) + " km\n"
        response += "Total cost of trip: $" + str(int(distancetravelled/priceperkm))[0:4]
        response += "\nThank you for using SwiftLift"
        resp.message(response)

        vloc = myrental.location()
        vinfo = myrental.info()
        users = User.query.all()
        user = None
        print("here are the users: ")
        print(User.query.all())
        for u in users:
            print(u.phonenumber)
            if u.phonenumber == request.values.get('From', None):
                user = u


        dt = datetime.datetime.now()
        minute = str(dt.minute)
        if dt.minute < 10:
            minute = "0" + str(dt.minute)
        time = str(dt.hour) + ":" + minute + ", " + str(dt.month) + "/" + str(dt.day) + "/" + str(dt.year)
        trip = Trip(startlat=str(startlat), startlon=str(startlon), endlat=str(vloc["data"]["latitude"]), endlon=str(vloc["data"]["longitude"]),
                distance=str(distancetravelled)+" km", car=str(vinfo["year"])  + " " + str(vinfo["make"]) + " " + str(vinfo["model"]),
                cost="$" + str(int(distancetravelled/priceperkm))[0:4], time=time, rider=user)
        db.session.add(trip)
        db.session.commit()
        carconfirmed = 0
    else:
        resp.message("Sorry, I didn't get that.")

    return str(resp)


#to check for cars in a 10-mile radius
def calc_distance(lata, longa, latb, longb):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lata)
    lon1 = radians(longa)
    lat2 = radians(latb)
    lon2 = radians(longb)
    dlon = abs(lon2 - lon1)
    dlat = abs(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance
