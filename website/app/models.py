from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    phonenumber = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    creditcard = db.Column(db.String(140))
    cvv = db.Column(db.String(140))
    expiration = db.Column(db.String(140))
    trips = db.relationship('Trip', backref='rider', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.phonenumber)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    startlat = db.Column(db.String(140))
    startlon = db.Column(db.String(140))
    endlat = db.Column(db.String(140))
    endlon = db.Column(db.String(140))
    distance = db.Column(db.String(140))
    car = db.Column(db.String(140))
    cost = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#    body = "Trip on " + str(timestamp) + " (" + car + ")"
#    body += "\nhttps://www.google.com/maps/dir/" + startlat + ",+" + startlon + "/" + endlat + ",+" + endlon
#    body += "\nTotal distance: " + distance + "\nTotal cost: " + cost + "\n"
    body = "Total distance: " + distance + "\n"
    def __repr__(self):
        return '<Trip {}>'.format(self.body)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
