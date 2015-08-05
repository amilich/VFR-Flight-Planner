from flask_wtf import Form
from wtforms import StringField, TextAreaField, SubmitField, validators, HiddenField, SelectField

"""
Home search page form for route and aircraft information. 
"""
class searchform(Form):
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
    dest = SelectField('Destination Airport: ', choices=options, default="KGON")
    speed = StringField('Cruising Speed (kts):', [validators.DataRequired()], default="110")
    alt = StringField('Altitude (feet):', [validators.DataRequired()], default="3500")
    climb = StringField('Climb Distance (nm):', [validators.DataRequired()], default="5")
    climb_speed = StringField('Climb Speed (kts):', [validators.DataRequired()], default="75")

    # airplane info
    # plane_type = StringField('Aircraft Make/Model:', [validators.DataRequired()], default="C172SP")
    # tail_num = StringField('Tail Number:', [validators.DataRequired()], default="N6228N")
    # empty_weight = StringField('Empty Weight (lbs):', [validators.DataRequired()], default="1733.7")
    # weight_arm = StringField('Weight Arm (in):', [validators.DataRequired()], default="41.476")
    # fuel_lbs = StringField('Fuel (lbs):', [validators.DataRequired()], default="318")
    # fuel_arm = StringField('Fuel arm (in):', [validators.DataRequired()], default="48")
    # pax1_lbs = StringField('Passenger Row 1 (lbs):', [validators.DataRequired()], default="300")
    # pax1_arm = StringField('Passenger Row 1 Arm (in):', [validators.DataRequired()], default="37")
    # pax2_lbs = StringField('Passenger Row 2 (lbs):', [validators.DataRequired()], default="0")
    # pax2_arm = StringField('Passenger Row 2 Arm (in):', [validators.DataRequired()], default="73")
    # bag1_lbs = StringField('Baggage 1 (lbs):', [validators.DataRequired()], default="0")
    # bag1_arm = StringField('Baggage 1 Arm (in):', [validators.DataRequired()], default="95")
    # bag2_lbs = StringField('Baggage 2 (lbs):', [validators.DataRequired()], default="0")
    # bag2_arm = StringField('Baggage 2 Arm (in):', [validators.DataRequired()], default="123")
    # climb_dist = StringField('Climb Distance (nm):', [validators.DataRequired()], default="10")
    # climb_speed = StringField('Climb Speed (kts):', [validators.DataRequired()], default="74")
    # descent_speed = StringField('Descent Speed (kts):', [validators.DataRequired()], default="90")
    # max_range = StringField('Maximum Range (nm):', [validators.DataRequired()], default="150")

"""
Form to change waypoint location with hidden waypoint number and user identified new location. 
"""
class placeform(Form):
    place = StringField('Origin Airport:', [validators.DataRequired()])
    num = HiddenField("num")

"""
Email feedback. 
"""
class ContactForm(Form):
    name = StringField('Your Name:', [validators.DataRequired()])
    email = StringField('Your e-mail address:', [validators.DataRequired(), validators.Email('your@email.com')])
    message = TextAreaField('Your message:', [validators.DataRequired()])
    #submit = SubmitField('Send Message')
