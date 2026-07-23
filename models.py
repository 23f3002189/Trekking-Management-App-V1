from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False) 
    is_approved = db.Column(db.Boolean, default=True) 
    full_name = db.Column(db.String(150), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    is_blacklisted = db.Column(db.Boolean, default=False)

class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    slots = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Open")
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    @property
    def booked_count(self):
        # Sums up all the slots_booked across all bookings for this trek
        return sum(b.slots_booked for b in self.bookings)

    @property
    def available_slots(self):
        return self.slots - self.booked_count

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Booked")
    user = db.relationship('User', backref='user_bookings') 
    trek = db.relationship('Trek', backref='bookings')
    slots_booked = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Float, default=0.0, nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'))
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    staff_rating = db.Column(db.Integer) 
    user_rating = db.Column(db.Integer)  
    comment = db.Column(db.Text)