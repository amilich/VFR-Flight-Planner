from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, validators, HiddenField, SelectField

"""
Home search page form for route and aircraft information. 
""" 
class searchform(FlaskForm):
    options = []
    # gather all the ICAO codes - more efficient to do it here because the same
    # options variable is used for 'orig' and 'dest'
    with open("data/us_airports.txt") as f: 
        lines = f.readlines() 
        for line in lines: 
            airpt = line.split(", ")[0]
            options.append((airpt, airpt))

    region = SelectField('Region: ', choices=[('Northeast', 'Northeast'), ('Southeast', 'Southeast'), ('Gulf', 'Gulf'), \
        ('West', 'North/South West'), ('WestCent', 'West Central'), ('Lakes', 'Great Lakes')], default="Northeast")
    orig = SelectField('Origin Airport: ', choices=options, default="KHPN")
    dest = SelectField('Destination Airport: ', choices=options, default="KATL")
    speed = StringField('Cruising Speed (kts):', [validators.DataRequired()], default="110")
    alt = StringField('Altitude (feet):', [validators.DataRequired()], default="3500")
    climb = StringField('Climb Distance (nm):', [validators.DataRequired()], default="5")
    climb_speed = StringField('Climb Speed (kts):', [validators.DataRequired()], default="75")

    # airplane info is dynamically added in index.html

"""
Form to change waypoint location with hidden waypoint number and user identified new location. 
"""
class placeform(FlaskForm):
    place = StringField('Origin Airport:', [validators.DataRequired()])
    num = HiddenField("num")

"""
Email feedback. 
"""
class ContactForm(FlaskForm):
    name = StringField('Your Name:', [validators.DataRequired()])
    email = StringField('Your e-mail address:', [validators.DataRequired(), validators.Email('your@email.com')])
    message = TextAreaField('Your message:', [validators.DataRequired()])
