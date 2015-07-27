from flask_wtf import Form
from wtforms import StringField, TextAreaField, SubmitField, validators, HiddenField

# for home search page
class searchform(Form):
    orig = StringField('Origin Airport:', [validators.DataRequired()], default="KHPN")
    dest = StringField('Destination Airport:', [validators.DataRequired()], default="KGON")
    speed = StringField('Cruising Speed (KTS):', [validators.DataRequired()], default="110")
    alt = StringField('Altitude (feet):', [validators.DataRequired()], default="3500")
    # airplane info
    plane_type = StringField('Aircraft Make/Model:', [validators.DataRequired()], default="C172SP")
    empty_weight = StringField('Empty Weight (lbs):', [validators.DataRequired()], default="1733.7")
    weight_arm = StringField('Weight Arm (in):', [validators.DataRequired()], default="41.476")
    fuel_lbs = StringField('Fuel (lbs):', [validators.DataRequired()], default="318")
    fuel_arm = StringField('Fuel arm (in):', [validators.DataRequired()], default="48")
    pax1_lbs = StringField('Passenger Row 1 (lbs):', [validators.DataRequired()], default="300")
    pax1_arm = StringField('Passenger Row 1 Arm (in):', [validators.DataRequired()], default="37")
    pax2_lbs = StringField('Passenger Row 2 (lbs):', [validators.DataRequired()], default="0")
    pax2_arm = StringField('Passenger Row 2 Arm (in):', [validators.DataRequired()], default="73")
    bag1_lbs = StringField('Baggage 1 (lbs):', [validators.DataRequired()], default="0")
    bag1_arm = StringField('Baggage 1 Arm (in):', [validators.DataRequired()], default="95")
    bag2_lbs = StringField('Baggage 2 (lbs):', [validators.DataRequired()], default="0")
    bag2_arm = StringField('Baggage 2 Arm (in):', [validators.DataRequired()], default="123")

# for changing location
class placeform(Form):
    place = StringField('Origin Airport:', [validators.DataRequired()])
    num = HiddenField("num")
    #submit = SubmitField('Send Message')

