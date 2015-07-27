from flask import Flask, render_template, g, Markup, session, request, redirect
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired
from FlightFiles import *
from forms import *
import os
from flask.ext.cache import Cache 
# flask cache extension; create app, cache

app = Flask(__name__)
app.secret_key = 'xbf\xcb7\x0bv\xcf\xc0N\xe1\x86\x98g9\xfei\xdc\xab\xc6\x05\xff%\xd3\xdf'
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

@app.route('/fplanner', methods = ['POST'])
def search():
	try: 
		airp1 = request.form['orig']
		airp2 = request.form['dest']
		altitude = request.form['alt']
		speed = request.form['speed']

		# need to get airplane parameters, store them in session
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

		session['ORIG'] = airp1
		session['DEST'] = airp2
		session['ALT'] = altitude
		session['SPD'] = speed

		# create the airplane *** TODO *** add tail number form
		airplane = Airplane("N6228N", craft_type, empty_weight, weight_arm, fuel_lbs, pax1_lbs, pax2_lbs, bag1_lbs, bag2_lbs, fuel_arm, pax1_arm, pax2_arm, bag1_arm, bag2_arm)

		try: 
			myRoute = createRoute(airp1, airp2, altitude, speed)
		except Exception,e: 
			print str(e)
		map_content = str(myRoute[0])

		forms = []
		counter = 0
		for x in range(len(myRoute[2].courseSegs)):
			forms.append(placeform(place=myRoute[2].courseSegs[x].to_poi.name, num=x))

		cache.set('myRoute', myRoute, timeout=300)
		return render_template('plan.html', map=Markup(map_content), theRoute = myRoute[2].courseSegs, forms=forms, page_title = "Your Route")
	except Exception, e: # really bad way...
		print str(e)
		newLoc = str(request.form['place'])
		num = str(request.form['num'])
		try: 
			myRoute = cache.get('myRoute')
			myRoute = changeRoute(myRoute[1], int(num)-1, str(newLoc), session['ORIG'], session['DEST'], session['ALT'], session['SPD'])
			print myRoute[1].courseSegs
			print myRoute[2].courseSegs
			map_content = str(myRoute[0])
			cache.set('myRoute', myRoute, timeout=300)

			forms = []
			counter = 0
			for x in range(len(myRoute[2].courseSegs)):
				forms.append(placeform(place=myRoute[2].courseSegs[x].to_poi.name, num=x))

			cache.set('myRoute', myRoute, timeout=300)
			return render_template('plan.html', map=Markup(map_content), theRoute = myRoute[2].courseSegs, forms=forms, page_title = "Your Route")
		except Exception, e: 
			print str(e)
			return '<a href="/">home</a>'

@app.route('/')
def init():
	form = searchform()
	return render_template('index.html', form=form)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)