# ./main.py
import smartcar
from flask import Flask, request, redirect, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# global variable to save our access_token
access = None

client = smartcar.AuthClient(
    client_id='906e6fc9-ee9e-4622-b19c-6055e4a7afe0',
    client_secret='9309bbfe-8de5-4a89-819e-6855b824bf3c',
    redirect_uri='http://localhost:8000/exchange',
    scope=['read_vehicle_info', 'read_location', 'read_odometer', 'control_security', 'control_security:unlock', 'control_security:lock'],
    #test_mode=True
)

@app.route('/login', methods=['GET'])
def login():
    auth_url = client.get_auth_url()
    return redirect(auth_url)


@app.route('/exchange', methods=['GET'])
def exchange():
    code = request.args.get('code')
    print(code)

    global access
    # in a production app you'll want to store this in some kind of
    # persistent storage
    access = client.exchange_code(code)
    return '', 200


@app.route('/vehicle', methods=['GET'])
def vehicle():
    global access
    # the list of vehicle ids
    vehicle_ids = smartcar.get_vehicle_ids(
        access['access_token'])['vehicles']

    vehicle = smartcar.Vehicle(vehicle_ids[0], access['access_token'])

    # TODO: Request Step 4: Make a request to Smartcar API
    info = vehicle.info()
    print("UWU\n\n\n\n\n")
    print(info)
    print("\n\n\nlocation\n\n\n")
    print(vehicle.location())

    return jsonify(info)


if __name__ == "__main__":
    app.run(port=8000)
