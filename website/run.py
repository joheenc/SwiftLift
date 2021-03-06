# /usr/bin/env python
# Download the twilio-python library from twilio.com/docs/libraries/python
import smartcar
from flask import Flask, request, redirect, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from flask_cors import CORS
from math import sin, cos, sqrt, atan2, radians

from app import app, db
from app.models import User, Trip


app = Flask(__name__)
CORS(app)

access = None
#user's location--hard-coded to Rutgers Student Center for now
userlat = 40.5055
userlong = -74.45188903808594

client = smartcar.AuthClient(
    client_id='906e6fc9-ee9e-4622-b19c-6055e4a7afe0',
    client_secret='9309bbfe-8de5-4a89-819e-6855b824bf3c',
    redirect_uri='http://localhost:8000/exchange',
    scope=['read_vehicle_info', 'read_location', 'read_odometer', 'control_security', 'control_security:unlock', 'control_security:lock'],
    #test_mode=True
)


@app.route('/auth', methods=['GET'])
def login():
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
    global carsconfirmed
    global myrental
    global startingmileage
    global priceperkm
    global startlat
    global startlon

    if carconfirmed == 0 and "rent a car" in text:
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
    elif carconfirmed == 0 and "Car" in text:
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
            carsconfirmed = 1
    elif carsconfirmed == 1 and "Confirm" in text:
    #    myrental.unlock()
        startingmileage = myrental.odometer()["data"]["distance"]
        response = "Ok, your rental has been confirmed! Your rental car has been unlocked.\nRespond with 'Done' when you are finished."
        resp.message(response)
    elif carsconfirmed == 1 and "Done" in text:
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
        for u in users:
            if u.phonenumber == request.values.get('From', None):
                user = u

        resp.message("Whoops, look like you haven't registered! Try again.")

        trip = Trip(startlat=str(startlat), startlon=str(startlon), endlat=str(vloc["data"]["latitude"]), endlon=str(vloc["data"]["longitude"]),
                distance=str(distancetravelled)+" km", car=str(vinfo["year"])  + " " + str(vinfo["make"]) + " " + str(vinfo["model"]),
                cost="$" + str(int(distancetravelled/priceperkm))[0:4], rider=user)
        db.session.add(trip)
        db.session.commit()
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


#if __name__ == "__main__":
#    app.run(debug=True, port=8000)
