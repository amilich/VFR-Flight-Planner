from __future__ import division
from fractions import Fraction
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
from LatLon import LatLon, Latitude, Longitude
from geomag import mag_heading
from BeautifulSoup import BeautifulSoup
from downloadmap import *
from Elevations import *
import urllib 
import re 
import sys 
import os 
import math 
import copy
import pygmaps 

"""
Objects and functions necessary for route planning. 
Airplanes, weights, environments, airports, cities, 
routes, and basic calculations. 

@class
	Airplane 
@class 
	Weight 
@class 
	Environment
@class 
	Point_Of_Interest
@class 
	Route 

@author: Andrew M. 
@date: 2015-2016
"""

"""
General conversion constants. 
"""
km_to_nm = 0.539957
km_to_miles = 0.621371
nm_to_km = 1.852
feet_to_nm = 0.000164579
meters_to_feet = 3.28084

"""
An airplane is used to store relevant information for weight and balance calculations. 
"""
class Airplane: 
	"""
	Initialize the plane with type and list of weights. 

	@type 	plane_type: string 
	@param 	plane_type: string of plane type (ex. "C172SP NAV III")
	@type 	weights: list 
	@param 	weights: list of weights with moments and arms
	"""
	def __init__(self, plane_type, weights): 
		self.plane_type = plane_type
		self.weights = weights
		for x in range(len(self.weights)): 
			self.weights[x].num = "Moment %i" % (x+1)
		self.calcCG()
		# ** NOTE ** need to log the tail number in database (can be done in App.py)
		return 

	"""
	Print the airplane type and CG as the representation of the airplane object. 
	"""
	def __repr__(self):
		return "Airplane of type: {" + self.plane_type + "} and CG=" + str(self.cg) + "."

	"""
	Calculates the center of gravity of an airpoane given each weight parameter 
	"""
	def calcCG(self):
		weight = 0
		moment = 0
		for item in self.weights: 
			weight += item.weight 
			moment += item.moment 
		if weight == 0: 
			self.cg = 0
			return
		self.cg = float("{0:.2f}".format(float(moment/weight)))
		self.totalweight = weight 
		self.totalmoment = moment
		return 

	"""
	Returns rows of performance data formatted in HTML for use in the weight and balance PDF. 
	"""
	def calcPerformance(self): 
		return 

	"""
	Calculates the maximum range for airplane 
		** NOTE ** must include 30 - 45 min reserve fuel. 
	"""
	def calcMaxRange(self):
		return 

"""
Generalized weight class with weight (lbs) and an arm (in) for CG calculations in any 
airplane type. 
"""
class Weight: 
	"""
	Initializes weight with moment, arm, and optional identifier. 

	@type 	weight: float 
	@param 	weight: weight (in lbs)
	@type 	arm: float 
	@param 	arm: moment arm (in)
	"""
	def __init__(self, weight, arm, num=0): 
		self.weight = weight 
		self.arm = arm 
		self.moment = self.weight*self.arm
		return 

	"""
	Shows weight, arm, and moment information. 
	"""
	def __repr__(self): 
		return "Weight: w=%s, a=%s, m=%s" % (self.weight, self.arm, self.moment)

"""
Creates environment for PDF of weather. 

@type 	icao: str 
@param 	icao: airport code
@rtype 	Environment 
@return environment with built in data
"""
def createEnvironment(icao):
	metar = getWeather(icao)
	return Environment(icao, metar)

"""
An environment can be used for weather, weight, balance, and performance calculations. 
"""
class Environment: 
	"""
	Set the environment parameters for given location. 

	@type 	location: str 
	@param 	location: airport code
	@type 	metar: str 
	@param 	metar: predetermined metar 
	"""
	def __init__(self, location, metar=""): 
		self.location = location # A point of interest (ex. airport)
		self.metar = metar if not metar=="" else getWeather(location) # set METAR 
		if not self.metar == "": 
			self.weather = "METAR"
		else: 
			self.weather = "NONE"
			return 
		self.winddir, self.wind = getWind(self.location, self.metar)
		self.time = Environment.getTime(self.metar)
		self.altimeter = Environment.getAltimeter(self.metar)
		self.visibility = Environment.getVisibility(self.metar)
		self.clouds = Environment.getClouds(self.metar) # CB clouds are only type shown
		self.elevation = getFieldElevation(self.location)
		self.wx = Environment.getWx(self.metar, self.clouds, self.visibility)
		self.skyCond = Environment.getSkyCond(self.metar, self.clouds, self.metar, self.wx)
		self.temp, self.dp = Environment.getTempDP(self.metar)
		self.pa = Environment.getPA(self.elevation, self.altimeter)
		self.da = Environment.getDA(self.pa, self.temp, self.elevation)
		return 

	"""
	Given METAR calculate the temperature and dewpoint. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@rType 	tuple 
	@return temperature and dewpoint
	"""
	@classmethod
	def getTempDP(cls, metar):
		for item in metar.split(): 
			if "/" in item and "FT" not in item and "SM" not in item: 
				temp = item.split("/")[0]
				dp = item.split("/")[1]
				return (temp, dp)
		return (0, 0)

	"""
	Given METAR calculate the observation time. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@rType 	string 
	@return the time of the METAR observation 
	"""
	@classmethod 
	def getTime(cls, metar): 
		for item in metar.split(): 
			if 'Z' == item[-1:]:
				return item
		return "000000Z"

	"""
	Given METAR return weather conditions/advisories. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@type 	clouds: string 
	@param 	clouds: cloud conditions
	@type 	visibility: int 
	@param 	visibility: visibility in SM
	@rType 	list  
	@return list of weather advisories 
	"""
	@classmethod 
	def getWx(cls, metar, clouds, visibility):
		for item in metar.split(): 
			if '-' in item or '+' in item: 
				return item 
		visInd = -1
		for x in range(len(metar.split())):
			if 'SM' in metar.split()[x]: 
				visInd = x
		cloudInd = -1
		for x in range(len(metar.split())): 
			if clouds[0] == metar.split()[x]:
				cloudInd = x
		if visInd + 1 == cloudInd: 
			return ""
		# the weather is between visibility and cloud conditions (always present)
		wx = metar.split()[visInd+1:cloudInd] 
		for item in wx: 
			if "R" in item[0] or "A" in item[0] or "RMK" in item: 
				wx.remove(item)
		if len(wx) > 1: 
			print 'length of wx > 1: %s; metar=%s' % (wx, metar)
			return ""
		return wx 

	"""
	Determine whether the weather is within VFR requirements. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@type 	clouds: string 
	@param 	clouds: cloud conditions
	@type 	visibility: int 
	@param 	visibility: visibility in SM
	@type 	wx: string 
	@param 	wx: weather advisories (ex. TS = thunderstorms)
	@rType 	string  
	@return current weather conditions
	"""
	# incorporate airspace!!! 
	@classmethod
	def getSkyCond(cls, metar, clouds, visibility, wx): 
		if 'TS' in wx: 
			return 'IFR' # should not fly VFR in vicinity of TS
		if "CLR" in str(clouds[0]) or "SKC" in str(clouds[0]): 
			clouds[0] += "999" # makes the rest of determining the ceiling easier  
		if clouds == "CLR" and visibility > 3: 
			return 'VFR'

		ceil = 100000
		for item in clouds: 
			if "BKN" in item or "OVC" in item: 
				ceil = float(item[3:].replace("CB", ""))*100
				break # ceiling is FIRST broken or overcast layer
		if ceil > 3000 and visibility > 3: 
			return 'VFR'
		elif ceil < 3000 and ceil > 1000 and \
		visibility > 3 and visibility < 5: 
			return 'SVFR'
		return 'IFR' # all other weather types are IFR or LIFR 

	"""
	Given METAR return the altimeter. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@rType 	float 
	@return altimeter setting 
	"""
	@classmethod
	def getAltimeter(cls, metar): 
		for item in metar.split(): 
			if 'A' in item[0] and item[1:].isdigit(): 
				return float(item[1:3] + "." + item[3:5]) 
		return 29.92

	"""
	Given METAR return the visibility. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@rType 	float 
	@return visibility 
	"""
	@classmethod 
	def getVisibility(cls, metar): 
		for item in metar.split(): 
			if 'SM'in item[-2:]: 
				try: 
					return int(float((item[:-2])))
				except: 
					x = Fraction(item[:-2])
					return int(x)
		return 0

	"""
	Given METAR return the cloud type and ceiling. 

	@type 	metar: string 
	@param 	metar: METAR information 
	@rType 	float 
	@return cloud conditions
	"""
	@classmethod 
	def getClouds(cls, metar):
		clouds = []
		if "RMK" in metar: 
			usable = metar.split("RMK")[0]
		else: 
			usable = metar 
		for item in usable.split(): 
			if 'SKC' in item or 'CLR' in item or 'FEW' in item or \
			   'SCT' in item or 'BKN' in item or 'OVC' in item: 
				clouds.append(item)
		if len(clouds) > 0: 
			return clouds 
		return "DATA ERROR"

	"""
	Calculate the pressure altitude. 

	@type 	elev: float 
	@param 	elev: field elevation
	@rType 	float 
	@return the pressure altitude
	"""
	@classmethod 
	def getPA(cls, elev, altimeter):
		press_diff = (altimeter - 29.92)*1000 # simple pressure altitude formula 
		return float(elev + press_diff)

	""" 
	Calculate the density altitude. 
	See http://www.flyingmag.com/technique/tip-week/calculating-density-altitude-pencil. 

	@type 	PA: float 
	@param 	PA: pressure altitude 
	@type 	temp: float 
	@param 	temp: air temperature (degrees C)
	@type 	alt: float 
	@param 	alt: altitude for calculation (usually field elevation)
	"""
	@classmethod 
	def getDA(cls, PA, temp, alt):
		ISA = 15 - math.floor(float(alt)/1000)*2
		return float(PA + 120*(float(temp)-ISA))

	"""
	Returns METAR (with almost all necessary information).  
	"""
	def __repr__(self):
		return self.metar 

"""
A point of interest can be an airport, city, or latitude/longitude location. It is used as origin and destination info for Segments. 
"""
class Point_Of_Interest:
	def __init__(self, name, lat, lon, dist=-1, data="", setting="normal"):
		self.name = name
		self.dist = dist
		self.lat = lat
		self.lon = lon
		self.priority = 0
		self.latlon = LatLon(Latitude(lat), Longitude(lon))
		self.data = data
		self.setting = setting
		return 

	# an initial qualification 
	def hasFuel(self): 
		try: 
			if(self.unicom != ""): 
				self.hasFuel = True 
		except: 
			self.hasFuel = False 

	def __repr__(self): 
		return str(self.name) + ": " +  str(self.dist)


"""
A route contains a list of segments and airplane parameters replated to a particular flight. 
"""
class Route: 
	def __init__(self, course, origin, destination, routeType="direct", night = False, custom=[], \
		cruising_alt=3500, cruise_speed=110, climb_speed=75, climb_dist=5, gph=10, descent_speed=90, doWeather=True, region="NORTHEAST"): 
		self.reset(course, origin, destination, routeType, night, custom, cruising_alt, cruise_speed, \
			climb_speed, climb_dist, gph, descent_speed, doWeather=doWeather, region=region)
		return 

	def reset(self, course, origin, destination, routeType, night, custom, cruising_alt, cruise_speed, \
		climb_speed, climb_dist, gph, descent_speed, climb_done=False, doWeather=False, region="NORTHEAST"): 
		self.origin = origin 
		self.destination = destination
		self.climb_speed = climb_speed
		self.climb_dist = climb_dist # nm, depends on cruising altitude - should become dynamic
		self.gph = gph
		self.fuelTaxi = 1.4
		self.routeType = routeType
		self.night = night
		self.errors = []
		self.cruising_alt = cruising_alt
		self.cruise_speed = cruise_speed
		self.descent_speed = descent_speed
		self.region = region
		# perform route calculations
		self.course = course 
		self.landmarks = custom
		if(routeType.lower() is not "direct" or climb_done): 
			self.courseSegs = createSegments(self.origin, self.destination, self.course, self.cruising_alt, self.cruise_speed, \
				self.climb_speed, self.descent_speed, custom=custom, isCustom=True, doWeather=doWeather, region=self.region)
			# using custom route or route with climb
		else: 
			self.courseSegs = createSegments(self.origin, self.destination, self.course, self.cruising_alt, self.cruise_speed, \
				self.climb_speed, self.descent_speed, custom=custom, doWeather=doWeather, region=self.region)
		for seg in self.courseSegs: 
			if seg.from_poi.name == seg.to_poi.name: 
				self.courseSegs.remove(seg)

		time = 0
		for item in self.courseSegs: 
			time += item.time
		self.time = time 
		self.minutes = float("{0:.2f}".format((self.time - math.floor(self.time))*60))
		self.hours = math.floor(self.time)

		self.calculateFuelTime()
		return 

	"""
	Takes a route and puts a climb in it 
		* TODO: insert climb before creating route. 
	"""
	def insertClimb(self): 
		if(self.course[0] < self.climb_dist): # someone 
			self.errors.append("Climb distance longer than route. Ignoring climb parameters.")
			print "Climb distance longer than route. Ignoring climb parameters." 
			# still adding landmarks 
			newLandmarks = [] 
			newLandmarks.append(self.origin)
			for x in range(len(self.courseSegs)): 
				newLandmarks.append(self.courseSegs[x].to_poi)
			self.landmarks = newLandmarks
			return 
		currentAlt = 0
		currentDist = 0
		remove = []
		if(self.courseSegs[0].length < self.climb_dist): 
			for x in range(len(self.courseSegs)):
				if(currentDist > self.climb_dist):
					break
				# climb distance is the LATERAL distance 
				currentDist += self.courseSegs[x].length
				if "custom" not in self.courseSegs[x].to_poi.setting: # TODO: check if this should also be from_poi
					remove.append(x)
		newLandmarks = [] 
		newLandmarks.append(self.origin)
		# now add TOC 
		heading = self.courseSegs[0].course[1] 
		offset = str(self.origin.latlon.offset(heading, float(self.climb_dist)*nm_to_km))
		offsetLatLon = (float(offset.split(", ")[0]), float(offset.split(", ")[1]))
		offsetObj = Point_Of_Interest("TOC", offsetLatLon[0], offsetLatLon[1])
		newLandmarks.append(offsetObj)
		for x in range(len(self.courseSegs)): 
			if x not in remove: 
				newLandmarks.append(self.courseSegs[x].to_poi)
		self.reset(self.course, self.origin, self.destination, self.routeType, self.night, newLandmarks, self.cruising_alt, \
			self.cruise_speed, self.climb_speed, self.climb_dist, self.gph, self.descent_speed, climb_done = True, doWeather = True, region=self.region)
		return 

	"""
	String representation. Used for storing in database.  
	"""
	def __repr__(self): 
		rep = ""
		for item in self.courseSegs: 
			rep += item 

	"""
	Calculates necessary amount of fuel for a flight. 
		* TODO: this method should be in Airplane class
	"""
	def calculateFuelTime(self): # fuel includes taxi; time does not
		# needs refinement 
		self.fuelRequired = 0
		self.time = 0
		self.totalDist = 0
		if self.night: 
			self.fuelRequired += 0.75*self.gph # 45 minute minimum reserve for night flights 
		else: 
			self.fuelRequired += 0.5*self.gph # 30 minute minimum reserve for day flights
		for leg in self.courseSegs: 
			self.time += leg.time 
			self.fuelRequired += leg.time*self.gph
			self.totalDist += leg.length
		self.fuelRequired += self.fuelTaxi
		return 


"""
Segments, which comprise a route, contain individual altitudes, headings, origins, destinations, wind, and other relevant pieces of data. 
"""
class Segment: 
	def __init__(self, from_poi, to_poi, true_hdg, alt, tas, isOrigin = False, isDest = False, num=0, aloft="0000+00"):
		# initialize arguments 
		self.from_poi = from_poi # Airport object 
		self.to_poi = to_poi # Airport object 
		self.true_hdg = true_hdg # Float 
		self.course = getDistHeading(from_poi, to_poi)
		self.true_hdg = self.course[1] # actual true heading! 
		self.alt = alt # Float 
		self.tas = tas # Float 
		self.isOrigin = isOrigin # Boolean 
		self.isDest = isDest # Boolean 
		self.num=num # integer
		self.aloft = aloft
		# initialize complex data
		self.length = from_poi.latlon.distance(to_poi.latlon)*km_to_nm # important! convert to miles
		self.magCorrect()
		self.getWindS()
		self.setCorrectedCourse()
		self.setGS()
		# time
		self.time = self.length/self.gs # distance/rate=time; in hours 
		self.minutes = float("{0:.2f}".format((self.time - math.floor(self.time))*60))
		self.hours = math.floor(self.time)
		self.totMinutes = self.time*60

		self.seg_hdg = float("{0:.2f}".format(from_poi.latlon.heading_initial(to_poi.latlon)))
		if(self.seg_hdg < 0): 
			self.seg_hdg += 360
		return 

	"""
	Correct for magnetic deviation. 
	"""
	def magCorrect(self): 
		self.mag_hdg = mag_heading(float(self.true_hdg), float(self.from_poi.lat), float(self.from_poi.lon)) # Get the magnetic heading 
		self.mag_var = float("{0:.2f}".format(getHeadingDiff(self.true_hdg, self.mag_hdg)))

	"""
	Calculates and sets wind correction angle. 
	"""
	def setCorrectedCourse(self): 
		wca = Segment.calcWindCorrectionAngle(self.true_hdg, self.tas, self.w, self.vw)
		self.wca = float("{0:.2f}".format(wca))
		self.hdg = float("{0:.2f}".format(self.mag_hdg + wca))
		return

	"""
	Calculates ground speed. 
	"""
	def setGS(self):
		self.gs = Segment.calcGroundSpeed(self.true_hdg, self.tas, self.w, self.vw)

	""" 
	Gets the wind for the segment. 
	"""
	def getWindS(self): 
		if(self.isOrigin or self.alt == 0): 
			self.w, self.vw = getWind(self.from_poi.name)
		else: 
			aloft = str(self.aloft)
			self.w = 10*float(aloft[:2]) # only 2 digits
			self.vw = float(aloft[2:4])
			if(len(aloft) > 4): 
				self.temp = float(aloft[4:])
		return 

	""" 
	Gets segment data to display to user. 
	"""
	def getData(self):
		return [self.from_poi.name, self.to_poi.name, str("{0:.2f}".format(self.length)), str(self.alt), str(self.tas), "{0:.2f}".format(float(self.gs)), str("{0:.2f}".format(self.totMinutes))]

	"""
	Converts segment to table entry. 

	@type 	num: int 
	@param 	num: the segment number (used for form) 
	@rtype 	string 
	@return string representation of segment 
	"""
	def convertToString(self, num): # for custom route planning
		try: 
			return "<td>" + self.from_poi.name + "</td><td>&rarr;</td><td>" + "<form action=\"/update\" method=\"post\"><input type='text' value='" + \
			self.to_poi.name + "' name=\"to\" readonly='false' ondblclick=\"this.readOnly='';\"> <input type=\"hidden\" name=\"num\" value=\"" + \
			str(num) + "\"> </form> " + "</td><td>" + str("{0:.2f}".format(self.length*km_to_nm))+ "</td><td>" + str(self.alt) + "</td><td>" + \
			str(self.tas) + "</td><td>" + str(self.gs) + "</td><td>" + str(self.hdg) + "</td>"
		except Exception,e: 
			print str(e) 

	"""
	Visual representation of segment. 
	"""
	def __repr__(self):
		return self.from_poi.name + " -> " + self.to_poi.name + " (" + str("{0:.2f}".format(self.length*km_to_nm)) + " mi, " + str(self.time) + " hrs); " + str(self.alt) + " @ " + str(self.tas) + " kt. GS=" + str(self.gs) + "; CH=" + str(self.hdg) + "." 
	
	@classmethod
	def calcWindCorrectionAngle(self, d, va, w, vw): # d is desired course, va true airspeed, w wind direction, vw wind speed
		# https://en.wikipedia.org/wiki/E6B
		va = float(va)
		vw = float(vw)
		d = float(d)
		w = float(w)
		ratio = vw/va
		return math.degrees(math.asin(ratio*math.sin(math.radians(w-d))))

	@classmethod
	def calcGroundSpeed(self, d, va, w, vw): 
		va = float(va)
		vw = float(vw)
		d = float(d)
		w = float(w)
		# https://en.wikipedia.org/wiki/E6B
		return math.sqrt(math.pow(va, 2) + math.pow(vw, 2) - 2*va*vw*math.cos(math.pi*(d-w+self.calcWindCorrectionAngle(d, va, w, vw))/180))

""" 
Retreives the METAR information from a particular airport. 

@type 	loc: Point_Of_Interest
@param 	loc: Airport used to get weather
@rtype 	str 
@return full METAR information 
"""
def getWeather(loc):
	if loc == "": 
		return ""
	try: 
		url = 'http://www.aviationweather.gov/adds/metars/?station_ids=%s&std_trans=standard&chk_metars=on&hoursStr=most+recent+only&submitmet=Submit' % (loc)
		page = urllib.urlopen(url)
		page = page.read()
		soup = BeautifulSoup(''.join(page))
		found = soup.findAll('font') # METAR data within font tag 
		return str(found).split(">")[1].split("<")[0]
	except: 
		return ""

"""
Finds the wind at a particular airport.

@type 	loc: Point_Of_Interest
@param 	loc: Airport used to get weather
@rtype 	tuple
@return tuple of wind direction and strength 
"""
def getWind(loc, metar=""):
	if not metar=="": 
		for item in metar.split():
			if "KT" in item: 
				winddir = item[0:3]
				windstrength = item[3:5]
				return (winddir, windstrength)
	weather = getWeather(loc)
	if weather == "": 
		return (0, 0)
	wind = ()
	for item in weather.split():
		if "CALM" in item: 
			return (0, 0)
		if "KT" in item: 
			winddir = item[0:3]
			windstrength = item[3:5]
			if ("VRB" in winddir): # cannot set particular direction or speed for variable wind
				return (0, 0)
			wind = (winddir, windstrength)
	return wind

"""
Pulls from all winds aloft sources on aviationweather.gov. 

@type 	lat: float
@param 	lon: Latitude to find winds aloft
@type 	lat: float
@param 	lon: Longitude to find winds aloft
@type 	alt: float
@param 	alt: Altitude to find winds aloft
@rtype 	str 
@return winds aloft (direction and velocity)
"""
def getWindsAloft(lat, lon, alt, region): 
	loc = Point_Of_Interest("windLoc", lat, lon)

	# base url for winds aloft: 'https://aviationweather.gov/products/nws/__location__'
	# all urls: ['https://aviationweather.gov/products/nws/boston', 'https://aviationweather.gov/products/nws/chicago', 
	# 'https://aviationweather.gov/products/nws/saltlakecity', 'https://aviationweather.gov/products/nws/sanfrancisco', 
	# 'https://aviationweather.gov/products/nws/miami', 'https://aviationweather.gov/products/nws/ftworth']

	found = []
	if "NORTHEAST" in region: 
		urls = ['https://aviationweather.gov/products/nws/boston']
	elif "SOUTHEAST" in region: 
		urls = ['https://aviationweather.gov/products/nws/miami']
	elif "GULF" in region: 
		urls = ['https://aviationweather.gov/products/nws/ftworth']
	elif "WEST" in region: 
		urls = ['https://aviationweather.gov/products/nws/sanfrancisco']
	elif "WESTCENT" in region:
		urls = ['https://aviationweather.gov/products/nws/saltlakecity']
	elif "LAKES" in region: 
		urls = ['https://aviationweather.gov/products/nws/chicago']
	else: 
		return "0000"

	# all winds aloft information 
	for url in urls: 
		page = urllib.urlopen(url)
		page = page.read()
		soup = BeautifulSoup(''.join(page))
		found += soup.findAll('pre')
	windLocs = []
	for line in str(found).split("\n"):
		if "pre" in line or "VALID" in line: 
			continue
		counter = 0
		# ignore winds aloft that do not have the full data by counting the number of pieces of data
		for item in line.split(" "): 
			if(item.strip() is not ""): 
				counter += 1
		if(counter < 10): 
			continue
		try: 
			airpt = str(line.split()[0])
			latlon = getLatLon(airpt)
			# put the winds aloft data in the airport object (speeds up later)
			windLocs.append(Point_Of_Interest(airpt, latlon[0], latlon[1], data=line))
		except:
			continue
	for item in windLocs: 
		item.dist = item.latlon.distance(loc.latlon)*km_to_nm
	sortedAirports = sorted(windLocs, key=lambda x: x.dist, reverse=False)

	dataLine = sortedAirports[0].data.split(" ")
	alt = float(alt)
	# information for winds aloft data - these are the altitude thresholds for each observation 
	# FT  3000    6000    9000   12000   18000   24000  30000  34000  39000 
	data = ""
	if alt >= 0 and alt < 4500: # 3000  
		data = dataLine[1]
	elif alt >= 4500 and alt < 7500: # 6000 
		data = dataLine[2]
	elif alt >= 7500 and alt < 10500: # 9000 
		data = dataLine[3]
	elif alt >= 10500 and alt < 15000: # 12000 
		data = dataLine[4]
	elif alt >= 15000 and alt < 21000: # 18000 
		data = dataLine[5]
	elif alt >= 21000 and alt < 27000: # 24000 
		data = dataLine[6]
	elif alt >= 27000 and alt < 32000: # 30000 
		data = dataLine[7]
	elif alt >= 32000 and alt < 36500: #34000 
		data = dataLine[8]
	elif alt >= 36500 and alt < 40000: #34000 
		data = dataLine[9]
	else: 
		data = "0000"
	if "9900" in data: # light and variable
		data = "0000"
	return data 

"""
Finds the distance and heading between two locations. 

@type 	poi1: Point_Of_Interest
@param 	poi1: Origin point 
@type 	poi2: Point_Of_Interest
@param 	poi2: Destination point 
@rtype 	tuple
@return distance and heading in tuple
"""
def getDistHeading(poi1, poi2): 
	try: 
		d = poi1.latlon.distance(poi2.latlon)*km_to_nm
		h = poi1.latlon.heading_initial(poi2.latlon)
		if h < 0: 
			h += 360 # sometimes gives negative headings which screws things up
		return (d, h)
	except: 
		'error'
		return (float("inf"), 0) #should be out of range, but need better fix

"""
Finds the distance between two airports (not POIs). 

@type 	icao1: string
@param 	icao1: origin airport
@type 	icao2: string
@param 	icao2: destination airport 
@rtype 	float 
@return distance 
"""
def getDist(icao1, icao2):
	ll1 = getLatLon(icao1)
	ll2 = getLatLon(icao2)
	latlon1 = LatLon(ll1[0], ll1[1])
	latlon2 = LatLon(ll2[0], ll2[1])
	d = latlon1.distance(latlon2)*km_to_nm
	print "route d: " + str(d)
	return d

"""
Finds latitude and longitude of airport from file.

@type 	icao: str 
@param 	icao: airport code
@rtype 	tuple
@return latitude and longitude 
"""
def getLatLon(icao):
	coords = ()
	with open("data/airports.txt") as f: # search in all airports, but use lare ones for landmarks
		lines = f.readlines()
		for line in lines: 
			data = line.split(", ")
			if icao in data[0]: #check vs ==
				coords = (data[1],data[2])
			else: 
				continue
	return coords 

"""
Finds the landmarks that are in range of an origin point. 

@type 	origin: Point_Of_Interest
@param 	origin: origin location 
@type 	dest: Point_Of_Interest
@param 	dest: destination location 
@type 	course: tuple
@param 	course: course heading and distance 
@rtype 	list
@return list of Point_Of_Interest 
"""
def getDistancesInRange(origin, dest, course): 
	distances = []
	originLoc = origin.latlon
	with open("data/newairports_2.txt") as f:
		lines = f.readlines()
		for line in lines: 
			data = line.split(", ")
			if(len(data) < 3): 
				continue
			temp = LatLon(Latitude(data[1]), Longitude(data[2]))
			tempDist = originLoc.distance(temp)*km_to_nm
			if(tempDist < math.ceil(course[0])): 
				distances.append(Point_Of_Interest(data[0], data[1], data[2], tempDist))
	
	with open("data/cities.txt") as f:
		lines = f.readlines()
		for line in lines: 
			data = line.split(", ")
			if(len(data) < 3): 
				continue
			temp = LatLon(Latitude(data[1]), Longitude(data[2]))
			tempDist = originLoc.distance(temp)*km_to_nm
			if(tempDist < math.ceil(course[0])):
				distances.append(Point_Of_Interest(data[0], data[1], data[2], tempDist))
	return distances 
 
"""
Calculates the difference between two headings. 

@type 	h1: float
@param 	h1: first heading 
@type 	h2: float
@param 	h2: second heading
@rtype 	tuple
@return latitude and longitude 
"""
def getHeadingDiff(h1, h2): 
	diff = h2 - h1
	absDiff = abs(diff)
	if(absDiff <= 180): 
		if(absDiff == 180): 
			return absDiff
		return diff 
	elif (h2 > h1): 
		return absDiff - 360
	return 360 - absDiff

"""
Determines if a location can be used as a subsequent landmark from a base point (ex. origin to first waypoint). 

@type 	base: Point_Of_Interest
@param 	base: base location to check if landmark is valid 
@type 	poi: Point_Of_Interest
@param 	poi: landmark to check
@type 	course: tuple
@param 	course: distance and heading of entire course 
@type 	tolerance: float 
@param 	tolerance: tolerance (slowly increased) for finding landmarks 
@rtype 	boolean 
@return whether landmark is valid
"""
def isValidLandmark(base, poi, course, tolerance): 
	l1 = base.latlon 
	l2 = poi.latlon
	tempDist = l1.distance(l2)*km_to_nm
	heading = l1.heading_initial(l2)

	base = 10
	if course[0] > 250: 
		base = 40

	if(tempDist < base*(1/tolerance) or tempDist > (base*2.5)*tolerance): # check tolerance math
		return False 
	if(abs(getHeadingDiff(heading, course[1])) < 20*tolerance):
		return True
	return False 

"""
Finds the prioritized landmarks from an origin location. 

@type 	origin: Point_Of_Interest
@param 	origin: base location 
@type 	validDistances: list
@param 	validDistances: all landmarks/airports in range 
@type 	course: tuple
@param 	course: distance and heading of entire course 
@type 	tolerance: float 
@param 	tolerance: tolerance for finding landmarks 
@rtype 	list 
@return prioritized list of landmarks 
"""
def getValidLandmarks(origin, validDistances, course, tolerance): 
	landmarks = []
	for airport in validDistances: 
		if(isValidLandmark(origin, airport, course, tolerance)): 
			landmarks.append(airport)
	finalMarks = []
	test = ""
	for item in landmarks: 
		if item.name in test: 
			continue 
		else: 
			finalMarks.append(item)
			test += item.name + " "
	return prioritizeLandmarks(finalMarks, origin, course)

"""
Prioritize the landmarks from a particular location. Prioritizes points of interests 
by heading difference, distance, and facility type (ex. town vs. airport). 

@type 	landmarks: list
@param 	landmarks: list of landmarks 
@type 	origin: Point_Of_Interest
@param 	origin: origin location 
@type 	course: tuple
@param 	course: course heading and distance 
@rtype 	list
@return ordered list of Point_Of_Interest objects (high to low priority)
"""
def prioritizeLandmarks(landmarks, origin, course): #only used by above method
	for landmark in landmarks: 
		if landmark.name.isupper():
			landmark.priority += 8 # tweak these numbers
		diff = abs(origin.latlon.heading_initial(landmark.latlon) - course[1])
		if diff < 5: 
			landmark.priority += 5
		if diff < 8: 
			landmark.priority += 3
		if diff < 10: 
			landmark.priority += 2
		dist = origin.latlon.distance(landmark.latlon)*km_to_nm
		if(abs(dist-20) < 5): 
			landmark.priority += 2
	sortedLandmarks = sorted(landmarks, key=lambda x: x.priority, reverse=True)
	return sortedLandmarks

"""
Find landmarks along duration of route. 

@type 	origin: Point_Of_Interest
@param 	origin: origin location 
@type 	destination: Point_Of_Interest
@param 	destination: destination location 
@type 	course: tuple
@param 	course: course heading and distance 
@rtype 	list
@return list of Point_Of_Interest objects 
"""
def calculateRouteLandmarks(origin, destination, course): 
	allRelevantAirports = getDistancesInRange(origin, destination, course) # work on SHORTENING this
	currentDist = course[0] # will be worked down to 0 (roughly)
	counter = 0
	routeLandmarks = []
	currentLandmark = origin 
	routeLandmarks.append(origin)
	while True or counter < 100: # in case the route is impossible
		if(currentDist < 25): 
			routeLandmarks.append(destination)
			break # your final landmark will be the end airport 
		else: 
			tolerance = 1
			currentLandmarks = getValidLandmarks(currentLandmark, allRelevantAirports, course, tolerance)
			while len(currentLandmarks) == 0: 
				# gradually increases tolerance
				tolerance += 0.3 
				currentLandmarks = getValidLandmarks(currentLandmark, allRelevantAirports, course, tolerance)
			currentLandmark = currentLandmarks[0]
			routeLandmarks.append(currentLandmark)
			currentDist = currentLandmark.latlon.distance(destination.latlon)*km_to_nm
		counter += 1
		course = getDistHeading(currentLandmark, destination)
	return routeLandmarks 

"""
Finds the field elevation of an airport. 

@type 	icao: str 
@param 	icao: airport code to find elevation 
@rtype	float 
@return the field elevation 
"""
def getFieldElevation(icao): 
	with open("data/airportalt.txt") as f:
		lines = f.readlines()
		for line in lines: 
			if icao in line: 
				alt = line.split(", ")[3]
				return float(alt)

"""
Finds a rough midpoint/median of a set of numbers - used to center map locations. 

@type 	num: int 
@param 	num: the length of the list 
@rtype 	int 
@return an index for the center
"""
def getMid(num): 
	if(num%2 == 0): 
		return int(num/2)
	return int((num-1)/2)

"""
Creates segments for a particular route. 

@type 	origin: Point_Of_Interest
@param 	origin: origin airport
@type 	destination: Point_Of_Interest
@param 	destination: destination airport 
@type 	course: tuple 
@param 	course: course heading and distance 
@type 	alt: int 
@param 	alt: altitude 
@type 	tas: int 
@param 	tas: route desired cruise speed 
@type 	climb_speed: int 
@param 	climb_speed: climb speed in knots  
@type 	descent_speed: int 
@param 	descent_speed: descending speed in knots 
@type 	custom: list 
@param 	custom: custom list of coordinates 
@type 	isCustom: boolean 
@param 	isCustom: whether route is customized 
@type 	doWeather: boolean 
@param 	doWeather: whether to input live weather 
@type 	region: string 
@param 	region: general region for winds aloft data 
@rtype 	int 
@return an index for the center
"""
def createSegments(origin, destination, course, alt, tas, climb_speed = 75, \
	descent_speed = 90, custom = [], isCustom=False, doWeather=True, region="NORTHEAST"): 
	if len(custom) == 0:
		landmarks = calculateRouteLandmarks(origin, destination, course)
	else: 
		landmarks = custom
	segments = []
	middle = len(landmarks)
	num = getMid(len(landmarks))

	if(doWeather):
		wAloft = getWindsAloft(landmarks[num].lat, landmarks[num].lon, alt, region)
	else: 
		wAloft = "0000+00"
	for x in range(len(landmarks)-1): 
		if x == 0: 
			# we want to use the METAR for the origin airport here 
			nextLeg = Segment(landmarks[x], landmarks[x+1], course[1], getFieldElevation(origin.name), climb_speed, True, False, x, aloft=wAloft) 
			# starting alt is field elevation 
		else: 
			nextLeg = Segment(landmarks[x], landmarks[x+1], course[1], alt, tas, num=x, aloft=wAloft) # ending is field elevation
		segments.append(nextLeg)
	return segments 

"""
Rounds number up to nearest thousand. 

@type 	num: float 
@param 	num: number to round 
@rtype 	float 
@return rounded number
"""
def roundthousand(num):
	return int(math.ceil(num/1000.0))*1000

"""
Finds a cruising altitude appropriate for route. 

@type 	origin: Point_Of_Interest
@param 	origin: origin location 
@type 	dest: Point_Of_Interest
@param 	dest: destination location 
@type 	course: tuple
@param 	course: course heading and distance 
@rtype 	float
@return proper cruising altitude 
"""
def getProperAlt(origin, destination, course):
	start = str(origin.latlon)
	end = str(destination.latlon)
	path = start + "|" + end
	elevations = getElevation(path, chartSize="700x200")
	# get the maximum altitude 
	maxAlt = max(elevations)
	# for hemispheric rule for cruising altitudes 
	start_lat = start.split(", ")[0]
	start_lon = start.split(", ")[1]
	mag_hdg = mag_heading(float(course[1]), float(start_lat), float(start_lon)) # Get the magnetic heading 

	cruise_alt = roundthousand(maxAlt*meters_to_feet)
	thousands = int(cruise_alt/1000)

	if mag_hdg >= 0 and mag_hdg <= 179: 
		if(thousands%2==0):
			cruise_alt += 1000 
	else: 
		if not thousands%2==0:
			cruise_alt += 1000 

	# for all VFR flights
	cruise_alt += 500 
	if(cruise_alt < 1500):
		cruise_alt += 2000

	pathMap = getChart(elevations)

	return (cruise_alt, pathMap)

"""
Creates route, map data, an elevation map, and relevant messages. 

@type 	home: str
@param 	home: origin airport code 
@type 	dest: str
@param 	dest: destination airport code 
@type 	altitude: float
@param 	altitude: desired cruising altitude (may be changed by application if inappropriate)
@type 	airspeed: float
@param 	airspeed: desired true airspeed 
@type 	custom: list
@param 	custom: custom list of landmarks 
@rtype 	tuple 
@return route segments, map code, elevation map, and messages
"""
def createRoute(home, dest, altitude, airspeed, custom=[], environments=[], climb_dist=7, climb_speed=75, region="NORTHEAST"): 
	messages = []

	ll = getLatLon(home)
	origin = Point_Of_Interest(home, ll[0], ll[1], 0)
	destination =  Point_Of_Interest(dest, getLatLon(dest)[0], getLatLon(dest)[1], -1)
	course = getDistHeading(origin, destination)
	
	elevation_data = getProperAlt(origin, destination, course)
	cruising_alt = elevation_data[0]
	elevation_map = elevation_data[1]
	final_alt = altitude
	if(float(cruising_alt) > float(altitude) or True): # TODO: should be if one is not even/odd etc. 
		final_alt = cruising_alt
		messages.append("Changed cruising altitude")
	rType = "direct" if len(custom) == 0 else "custom"
	route = Route(course, origin, destination, routeType=rType, custom=custom, cruising_alt=final_alt, cruise_speed=airspeed, \
		climb_speed=climb_speed, climb_dist=climb_dist, doWeather=False, region=region)

	noTOC = copy.copy(route)
	route.insertClimb()
	messages.append("Added Top of Climb (TOC) waypoint")

	# map creation
	num = getMid(len(route.courseSegs))
	mapLL = (route.courseSegs[num].to_poi.lat, route.courseSegs[num].to_poi.lon)
	mymap = pygmaps.maps(float(mapLL[0]), float(mapLL[1]), 7)
	mymap.addpoint(float(ll[0]), float(ll[1]))
	path = []
	path.append((float(ll[0]), float(ll[1])))
	frequencies = getFrequencies(route.courseSegs)
	# route path line 
	for item in route.courseSegs: 
		path.append((float(item.to_poi.lat), float(item.to_poi.lon)))
		if item.to_poi.hasFuel: # this will not work if frequencies have not yet been set
			# some fuel/gas sign here - clipart type thing 
			mymap.addpoint(float(item.to_poi.lat), float(item.to_poi.lon))
		else: 
			# no discrimination based on fuel currentlyforms
			mymap.addpoint(float(item.to_poi.lat), float(item.to_poi.lon))
		# add point with fuel or not 

	mymap.addpath(path,"#4169E1")
	return (getHtml(mymap, route.landmarks), noTOC, route, elevation_map, messages, frequencies, getZip(origin))
 
"""
Creates a static map for PDF viewing. Alternatively could use a 
URL encoder, but complications arose with duplicate parameters 
and complicated paths. 

@type 	segments: list 
@param 	segments: list of route segments
@type 	destination: Point_Of_Interest
@param 	destination: destination location 
@rtype 	string 
@return static map image url 
"""
def makeStaticMap(segments,destination):
	base_url = "https://maps.googleapis.com/maps/api/staticmap?&size=500x200&maptype=terrain" 
	num = 1 # number each label on map
	if len(segments) < 10: 
		for item in segments: 
			base_url += "&markers=color:blue%%7Clabel:%s%%7C%s,%s" % \
						(num, item.from_poi.lat, item.from_poi.lon)
			num += 1
		base_url += "&markers=color:blue%%7Clabel:%s%%7C%s,%s" % \
					(num, destination.lat, destination.lon)
	# add red path
	base_url += "&path=color:red%7Cweight:5%7C"
	for item in segments: 
		base_url +=  str(item.from_poi.lat) + "," + str(item.from_poi.lon) + "%7C"
	base_url += str(destination.lat) + "," + str(destination.lon)
	return base_url

"""
Collects useful VFR frequencies for a given airport. 
Ignores approach, clearance delivery, and departure 
frequencies. 

@type 	segments: list 
@param 	segments: list of segments in route 
@rtype	list
@return list of frequencies
"""
def getFrequencies(segments, setUnicom=False):
	freqs = [] 
	airports = [] 
	for item in segments: 
		if len(item.from_poi.name) == 4: 
			airports.append(item.from_poi.name) 
	airports.append(segments[len(segments)-1].to_poi.name)

	with open("data/us-frequencies.csv", "r+") as f: 
		lines = f.readlines() 
		for item in airports: 
			for line in lines: 
				if item == line.split(",")[2]:
					# if line.split(",")[3] in "ATIS CTAF TWR GND UNIC FSS EFAS CNTR": 
					freqs.append(line.replace("\n", "").split(",")[2:6])

	currentAirport = ""
	# makes it easier to see in table format if airport code only shown for 1st airport
	for item in freqs: 
		if item[0] == currentAirport: 
			for seg in segments: 
				if seg.from_poi.name == currentAirport: 
					if item[1] == "UNICOM": 
						segments[-1].to_poi.unicom = item[-1] # last item should be frequency - NEEDS VERIFICATION
			if segments[-1].to_poi.name == currentAirport: 
				if item[1] == "UNICOM": 
					segments[-1].to_poi.unicom = item[-1] # last item should be frequency - NEEDS VERIFICATION
			item[0] = "" 
		else: 
			currentAirport = item[0]
	return freqs 

"""
Get zipcode for an airport. 

@type 	loc: Point_Of_Interest
@param 	loc: airport 
@rtype 	string 
@return the zipcode 
"""
def getZip(poi):
	try: 
		geolocator = Nominatim()
		location = geolocator.reverse((poi.lat, poi.lon))
		zipcode = "" 
		for item in str(location.address).split(", "): 
			if item.isdigit(): 
				zipcode = item 
		return zipcode
	except: 
		print 'WX Fail %s' % (poi.name) # for weather radar 
		return ""

"""
Gets potential points of interest from a file. 

@type 	filename: string 
@param 	filename: file to get data 
@type 	p: string 
@param 	p: the place you're looking for
@type 	prevLoc: Point_Of_Interest
@param 	prevLoc: base location
@type 	r: route
@param 	r: entire route 
@type 	allowSpaces: boolean 
@param 	allowSpaces: the place you're looking for
@rtype 	list 
@return Point_Of_Interest list
"""
def getData(filename, p, prevLoc, r, allowSpaces = False):
	potChanges = []
	with open(filename) as f:
		lines = f.readlines()
		for line in lines: 
			data = line.split(", ")
			if(len(data) < 3 or p.lower().replace(" ", "") not in data[0].replace(" ", "").lower()): 
				continue
			temp = LatLon(Latitude(data[1]), Longitude(data[2]))
			tempDist = prevLoc.latlon.distance(temp)*km_to_nm
			if(tempDist < 2*math.ceil(r.course[0])): # still lets you route a course through new location that may be further away 
				potChanges.append(Point_Of_Interest(data[0], data[1], data[2], tempDist))
	return potChanges

"""
Changes a particular landmark along a route and returns a new route. 
"""
def changeRoute(r, n, p, home, dest, altitude, airspeed, climb_dist, climb_speed, region): 
	# route, leg # to change, where to change it to 
	print 'changing route from %s to %s at segment %i to: %s' % (home, dest, n, p)
	prevLoc = r.courseSegs[n].from_poi
	potChanges = []
	potChanges += (getData("data/cities.txt", p, prevLoc, r, True))
	potChanges += (getData("data/airports.txt", p, prevLoc, r, True))
	selectedChange = sorted(potChanges, key=lambda x: x.dist, reverse=False)[0]
	# it will now select the closest one
	prevLandmarks = []
	for item in r.courseSegs: 
		prevLandmarks.append(item.from_poi)
	prevLandmarks.append(item.to_poi)
	newLandmarks = list(prevLandmarks)
	selectedChange.setting = "custom"
	newLandmarks[n+1] = selectedChange # increment by one because you are using the TO poi (+1)
	return createRoute(home, dest, altitude, airspeed, newLandmarks, climb_dist = climb_dist, climb_speed=climb_speed, region=region)

"""
For encoding all route parameters in a database. 
"""
def encodeRoute(r): 
	return

"""
For decoding a route from database. 
"""
def decodeRoute(r):
	return 

"""
Looks at wind patterns to determine best altitude to fly at. 
"""
def findBestAlt(lat, lon, region, cruise_alt): 
	w_1 = getWindsAloft(lat, lon, region, cruise_alt)
	w_2 = getWindsAloft(lat, lon, region, cruise_alt+2000)
	w_3 = getWindsAloft(lat, lon, region, cruise_alt+4000)
	# should probably be run from route page
	# sort from possible hemisphere route altitudes for VFR flight 
	# look at winds aloft at different altitudes. 
	# strongest wind*cos(wind_vector - route_vector)
	# display new possible times for route at different altitudes 
	return 