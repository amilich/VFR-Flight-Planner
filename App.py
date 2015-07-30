from flask import Flask, render_template, g, Markup, session, request, redirect, make_response
from flask_wtf import Form
from flask_mail import Mail, Message
from wtforms import StringField
from wtforms.validators import DataRequired
from pdf import gen_pdf 
from FlightFiles import *
from flask.ext.cache import Cache 
from forms import *
import os
# flask cache extension; create app, cache

app = Flask(__name__)
app.secret_key = 'xbf\xcb7\x0bv\xcf\xc0N\xe1\x86\x98g9\xfei\xdc\xab\xc6\x05\xff%\xd3\xdf'
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

gmail_name = 'codesearch5@gmail.com'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = gmail_name
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_KEY')
mail = Mail(app)

@app.route('/savewb')
def saveWeightBalance():
	print 'wb'
	return render_template('index.html')

@app.route('/saveplan', methods=['GET'])
def savePlan(): 
	try: 
		myRoute = cache.get('myRoute')
		map_content = str(makeStaticMap(myRoute[2].courseSegs, myRoute[2].destination)).replace("\n", "")
		route_pdf = gen_pdf(render_template('pdfroute.html', map=Markup(map_content), theRoute = myRoute[2].courseSegs, elevation=myRoute[3]))
		response = make_response(route_pdf)
		response.mimetype = 'application/pdf'
		response.headers["Content-Disposition"] = "attachment; filename=route.pdf"
		return response
	except Exception, e: 
		print str(e)
		return "PDF generation failed."

# for route changes
@app.route('/update', methods = ['POST'])
def update():
	newLoc = str(request.form['place'])
	num = str(request.form['num'])
	try: 
		myRoute = cache.get('myRoute')
		myRoute = changeRoute(myRoute[1], int(num)-1, str(newLoc), session['ORIG'], session['DEST'], session['ALT'], session['SPD'])
		map_content = str(myRoute[0])
		cache.set('myRoute', myRoute, timeout=300)

		forms = []
		counter = 0
		for x in range(len(myRoute[2].courseSegs)):
			forms.append(placeform(place=myRoute[2].courseSegs[x].to_poi.name, num=x))

		cache.set('myRoute', myRoute, timeout=300)
		return render_template('plan.html', map=Markup(map_content), theRoute = myRoute[2].courseSegs, forms=forms, page_title = "Your Route", elevation=myRoute[3])
	except Exception, e: 
		print str(e)
		return '<a href="/">home</a>'

@app.route('/fplanner', methods = ['POST'])
def search():
	# render_template("flightplan.html")
	airp1 = request.form['orig'].upper()
	airp2 = request.form['dest'].upper()
	altitude = request.form['alt']
	speed = request.form['speed']

	# need to get airplane parameters, store them in session
	tail_num = request.form['tail_num']
	craft_type = request.form['plane_type']
	empty_weight = request.form['empty_weight']
	weight_arm = request.form['weight_arm']
	fuel_lbs = request.form['fuel_lbs'] 
	fuel_arm = request.form['fuel_arm'] 
	pax1_lbs = request.form['pax1_lbs']
	pax1_arm = request.form['pax1_arm']
	pax2_lbs = request.form['pax2_lbs']
	pax2_arm = request.form['pax2_arm']
	bag1_lbs = request.form['bag1_lbs']
	bag1_arm = request.form['bag1_arm']
	bag2_lbs = request.form['bag2_lbs']
	bag2_arm = request.form['bag2_arm']
	# create the airplane
	airplane = Airplane(tail_num, craft_type, empty_weight, weight_arm, fuel_lbs, pax1_lbs, pax2_lbs, bag1_lbs, bag2_lbs, fuel_arm, pax1_arm, pax2_arm, bag1_arm, bag2_arm)
	cache.set('plane', airplane, timeout=300)

	session['ORIG'] = airp1
	session['DEST'] = airp2
	session['ALT'] = altitude
	session['SPD'] = speed

	myRoute = createRoute(airp1, airp2, altitude, speed)
	map_content = str(myRoute[0])

	forms = []
	counter = 0
	for x in range(len(myRoute[2].courseSegs)):
		forms.append(placeform(place=myRoute[2].courseSegs[x].to_poi.name, num=x))
	
	cache.set('myRoute', myRoute, timeout=300)
	messages = myRoute[4]

	showMsgs = False 
	if(len(messages) is not 0): 
		showMsgs = True

	msg = Message("Route planned from " + airp1 + " to " + airp2, sender="codesearch5@gmail.com", recipients=['codesearch5@gmail.com']) 
	# can attach pdf of route
	# msg.body = str(myRoute[2].courseSegs)[1:-1]
	# route_pdf = gen_pdf(render_template('plan.html', map="", theRoute = myRoute[2].courseSegs, forms=forms, page_title = "Your Route", elevation=myRoute[3], messages=messages, showMsgs = False))
	# msg.attach("route.pdf", "application/pdf", route_pdf)
	mail.send(msg)

	return render_template('plan.html', map=Markup(map_content), theRoute = myRoute[2].courseSegs, forms=forms, page_title = "Your Route", elevation=myRoute[3], messages=messages, showMsgs = showMsgs)

@app.route('/')
def init():
	form = searchform()
	return render_template('index.html', form=form)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.debug = True 
    app.run(host='0.0.0.0', port=port)