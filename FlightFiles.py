from __future__ import division
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
from LatLon import LatLon, Latitude, Longitude
from geomag import mag_heading
from BeautifulSoup import BeautifulSoup
from downloadmap import *
from Elevations import *
import urllib, re, sys, os, math, copy
import pygmaps 

"""
	TODO: 
		Climbs across waypoints 
		Fuel stops (unicom, etc.)
		Simple weight and balance 
		Add loading page for update routes 
		[DONE] Elevation awareness and maps 

	Possible inefficiencies: 
		Should search for waypoints after TOC 

"""
# conversion constants
km_to_nm = 0.539957
km_to_miles = 0.621371
nm_to_km = 1.852
feet_to_nm = 0.000164579
meters_to_feet = 3.28084

# An airplane is used to store relevant information for weight and balance calculations
class Airplane: 
	# ** NOTE ** for now, all data is for C172 
	def __init__(self, tail_number, plane_type, empty_weight, empty_arm, fuel, pax1, pax2, bag1, bag2, fuel_arm=48, pax1_arm=37, pax2_arm=73, bag1_arm=95, bag2_arm=123):
		self.tail = tail_number
		self.plane_type = plane_type
		self.empty_weight = empty_weight 
		self.empty_arm = empty_arm
		self.fuel = fuel 
		self.pax1 = pax1 
		self.pax2 = pax2 
		self.bag1 = bag1 
		self.bag2 = bag2 
		self.fuel_arm = fuel_arm 
		self.pax1_arm = pax1_arm
		self.pax2_arm = pax2_arm
		self.bag1_arm = bag1_arm
		self.bag2_arm = bag2_arm
		self.calcCG()

		# ** NOTE ** need to log the tail number in database (can be done in App.py)

	def __repr__(self):
		return "I am an airplane of type: {" + self.plane_type + "} and CG=" + str(self.cg) + "."

	"""
	Calculates the center of gravity of an airpoane given each weight parameter 
	"""
	def calcCG(self):
		self.weight = float(self.empty_weight) + float(self.fuel) + float(self.pax1) + float(self.pax2) + float(self.bag1) + float(self.bag2)
		self.moment = float(self.empty_weight)*float(self.empty_arm) + float(self.fuel)*float(self.fuel_arm) + float(self.pax1)*float(self.pax1_arm) + float(self.pax2)*float(self.pax2_arm) + float(self.bag1)*float(self.bag1_arm) + float(self.bag2)*float(self.bag2_arm)
		self.cg = self.moment/self.weight
		return 

	# calculates the maximum range for airplane ** NOTE ** must include 30 - 45 min reserve fuel 
	def calcMaxRange(self):
		return 

	def createWeightBalance(self):
		return 

# An environment can be used for weather, weight, balance, and performance calculations. 
class Environment: 
	# set the environment parameters from weather 
	def __init__(self, location, temp, pres, elevation, sky_cond, visibility): 
		self.location = location # A point of interest (ex. airport)
		self.temp = temp
		self.pres = pres 
		self.elevation = elevation
		self.sky_cond = sky_cond 
		self.visibility = visibility
		return 

	# pressure alt
	def calcPressureAltitude(self):
		press_diff = (self.pres - 29.92)*1000
		return 

	# density alt
	def calcDensityAltitude(self):
		return 

	# VFR or IFR 
	def calcFlightConditions(self):
		return 

# A point of interest can be an airport, city, or latitude/longitude location. It is used as origin and destination info for Segments. 
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
	def __repr__(self): 
		return str(self.name) + ": " +  str(self.dist)

# Segments, which comprise a route, contain individual altitudes, headings, origins, destinations, wind, and other relevant pieces of data
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
		print self.length
		self.magCorrect()
		self.getWind()
		self.setCorrectedCourse()
		self.setGS()
		# time
		self.time = self.length/self.gs # distance/rate=time

	# correct for magnetic deviation
	def magCorrect(self): 
		self.mag_hdg = mag_heading(float(self.true_hdg), float(self.from_poi.lat), float(self.from_poi.lon)) # Get the magnetic heading 

	# calculates and sets wind correction angle
	def setCorrectedCourse(self): 
		wca = Segment.calcWindCorrectionAngle(self.true_hdg, self.tas, self.w, self.vw)
		self.hdg = self.mag_hdg + wca
		return

	# calculates ground speed
	def setGS(self):
		self.gs = Segment.calcGroundSpeed(self.true_hdg, self.tas, self.w, self.vw)

	def getWind(self): 
		if(self.isOrigin or self.alt == 0): 
			self.w, self.vw = getWind(self.from_poi.name)
		elif(self.isDest or self.alt == 0):
			self.w, self.vw = getWind(self.to_poi.name)
		else: 
			# aloft = getWindsAloft(self.from_poi.lat, self.from_poi.lon, self.alt)
			aloft = str(self.aloft)
			#if("9900" in str(aloft)): 
			#	aloft = "0000+00"
			self.w = 10*aloft[:2] # only 2 digits
			self.vw = aloft[2:4]
			self.temp = aloft[4:]
		return 

	def getData(self):
		return [self.from_poi.name, self.to_poi.name, str("{0:.2f}".format(self.length)), str(self.alt), str(self.tas), str(self.gs), str(self.hdg)]

	def convertToString(self, num): # for custom route planning
		try: 
			return "<td>" + self.from_poi.name + "</td><td>&rarr;</td><td>" + "<form action=\"/update\" method=\"post\"><input type='text' value='" + self.to_poi.name + "' name=\"to\" readonly='false' ondblclick=\"this.readOnly='';\"> <input type=\"hidden\" name=\"num\" value=\"" + str(num) + "\"> </form> " + "</td><td>" + str("{0:.2f}".format(self.length*km_to_nm))+ "</td><td>" + str(self.alt) + "</td><td>" + str(self.tas) + "</td><td>" + str(self.gs) + "</td><td>" + str(self.hdg) + "</td>"
		except Exception,e: 
			print str(e) 

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
def getWind(loc):
	weather = getWeather(loc)
	wind = ()
	for item in weather.split():
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
def getWindsAloft(lat, lon, alt): 
	loc = Point_Of_Interest("windLoc", lat, lon)

	# base url for winds aloft: 'https://aviationweather.gov/products/nws/boston'
	urls = ['https://aviationweather.gov/products/nws/boston', 'https://aviationweather.gov/products/nws/chicago', 'https://aviationweather.gov/products/nws/saltlakecity', 'https://aviationweather.gov/products/nws/sanfrancisco', 'https://aviationweather.gov/products/nws/miami', 'https://aviationweather.gov/products/nws/ftworth']
	found = []

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
	# information for winds aloft data 
	# FT  3000    6000    9000   12000   18000   24000  30000  34000  39000 
	if alt >= 0 and alt < 4500: # 3000  
		return dataLine[1]
	elif alt >= 4500 and alt < 7500: # 6000 
		return dataLine[2]
	elif alt >= 7500 and alt < 10500: # 9000 
		return dataLine[3]
	elif alt >= 10500 and alt < 15000: # 12000 
		return dataLine[4]
	elif alt >= 15000 and alt < 21000: # 18000 
		return dataLine[5]
	elif alt >= 21000 and alt < 27000: # 24000 
		return dataLine[6]
	elif alt >= 27000 and alt < 32000: # 30000 
		return dataLine[7]
	elif alt >= 32000 and alt < 36500: #34000 
		return dataLine[8]
	elif alt >= 36500 and alt < 40000: #34000 
		return dataLine[9]
	else: 
		print 'ret 0'
		return "0000"

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
		return (poi1.latlon.distance(poi2.latlon)*km_to_nm, poi1.latlon.heading_initial(poi2.latlon))
	except: 
		'error'
		return (float("inf"), 0) #should be out of range, but need better fix

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

# gets the landmarks that are in range of an origin point 
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

# determines if a location can be used as a subsequent landmark from a base point (ex. origin to first waypoint)
def isValidLandmark(base, poi, course, tolerance): 
	l1 = base.latlon 
	l2 = poi.latlon
	tempDist = l1.distance(l2)*km_to_nm
	heading = l1.heading_initial(l2)
	if(tempDist < 10*(1/tolerance) or tempDist > 25*tolerance): # check tolerance math
		return False 
	if(abs(getHeadingDiff(heading, course[1])) < 20*tolerance):
		return True
	return False 

# finds the prioritized landmarks from an origin location
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

# prioritizes points of interests by heading difference, distance, and facility type (ex. town vs. airport)
def prioritizeLandmarks(landmarks, origin, course): #only used by above method
	for landmark in landmarks: 
		if landmark.name.isupper():
			#print 'airport'
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

# find a list of landmarks to comprise the route
def calculateRouteLandmarks(origin, destination, course): 
	allRelevantAirports = getDistancesInRange(origin, destination, course)

	currentDist = course[0] # will be worked down to 0 (roughly)
	counter = 0
	routeLandmarks = []
	currentLandmark = origin 
	routeLandmarks.append(origin)
	while True or counter < 100: # in case the route is impossible
		if(currentDist*km_to_nm < 28): 
			routeLandmarks.append(destination)
			break # your final landmark will be the end airport 
		else: 
			tolerance = 1
			currentLandmarks = getValidLandmarks(currentLandmark, allRelevantAirports, course, tolerance)
			while len(currentLandmarks) == 0: 
				# gradually increases tolerance
				tolerance += 0.1
				currentLandmarks = getValidLandmarks(currentLandmark, allRelevantAirports, course, tolerance)
			currentLandmark = currentLandmarks[0]
			routeLandmarks.append(currentLandmark)
			currentDist = currentLandmark.latlon.distance(destination.latlon)*km_to_nm
		counter += 1
		course = getDistHeading(currentLandmark, destination)
	return routeLandmarks 

# finds the field elevation of an airport
def getFieldElevation(icao): 
	with open("data/airportalt.txt") as f:
		lines = f.readlines()
		for line in lines: 
			if icao in line: 
				alt = line.split(", ")[3]
				return float(alt)

# finds a rough midpoint/median of a set of numbers
# used to center map locations
def getMid(num): 
	if(num%2 == 0): 
		return int(num/2)
	return int((num-1)/2)

# creates segments for a particular route
def createSegments(origin, destination, course, alt, tas, climb_speed = 75, descent_speed = 90, custom = [], isCustom=False, doWeather=True): 
	if len(custom) == 0:
		landmarks = calculateRouteLandmarks(origin, destination, course)
	else: 
		landmarks = custom
	segments = []
	middle = len(landmarks)
	num = getMid(len(landmarks))

	if(doWeather):
		wAloft = getWindsAloft(landmarks[num].lat, landmarks[num].lon, alt)
	else: 
		wAloft = "0000+00"

	for x in range(len(landmarks)-1): # - 2 bc final in last thing?
		if x == 0: 
			nextLeg = Segment(landmarks[x], landmarks[x+1], course[1], getFieldElevation(origin.name), climb_speed, True, False, x, aloft=wAloft) # starting alt is field elevation 
		#elif x == len(landmarks)-2 and len(landmarks) is not 3: # we do not want field elevation here
		#	nextLeg = Segment(landmarks[x], landmarks[x+1], course[1], getFieldElevation(destination.name), descent_speed, False, True, x) # ending is field too
		else: 
			nextLeg = Segment(landmarks[x], landmarks[x+1], course[1], alt, tas, num=x, aloft=wAloft) # ending is field elevation
		segments.append(nextLeg)
	return segments 

class Route: 
	def __init__(self, course, origin, destination, routeType="direct", night = False, custom=[], cruising_alt=3500, cruise_speed=110, climb_speed=75, climb_dist=7, gph=10, descent_speed=90, doWeather=True): 
		self.reset(course, origin, destination, routeType, night, custom, cruising_alt, cruise_speed, climb_speed, climb_dist, gph, descent_speed, doWeather=doWeather)

	def reset(self, course, origin, destination, routeType, night, custom, cruising_alt, cruise_speed, climb_speed, climb_dist, gph, descent_speed, climb_done=False, doWeather=False): 
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
		# perform route calculations
		self.course = course 
		if(routeType.lower() is not "direct" or climb_done): 
			self.courseSegs = createSegments(self.origin, self.destination, self.course, self.cruising_alt, self.cruise_speed, self.climb_speed, self.descent_speed, custom=custom, isCustom=True, doWeather=doWeather)
			# using custom route or route with climb
		else: 
			self.courseSegs = createSegments(self.origin, self.destination, self.course, self.cruising_alt, self.cruise_speed, self.climb_speed, self.descent_speed, custom=custom, doWeather=doWeather)
		for seg in self.courseSegs: 
			if seg.from_poi.name == seg.to_poi.name: 
				self.courseSegs.remove(seg)
		self.calculateFuelTime()

	# takes a route and puts a climb in it - TODO: do before creating route
	def insertClimb(self): 
		if(self.course[0] < self.climb_dist): # someone 
			self.errors.append("Climb distance longer than route. Ignoring climb parameters.")
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
		print 'offset: ' + str(self.climb_dist*nm_to_km)
		offset = str(self.origin.latlon.offset(heading, float(self.climb_dist)*nm_to_km))
		offsetLatLon = (float(offset.split(", ")[0]), float(offset.split(", ")[1]))
		offsetObj = Point_Of_Interest("TOC", offsetLatLon[0], offsetLatLon[1])
		newLandmarks.append(offsetObj)
		for x in range(len(self.courseSegs)): 
			if x not in remove: 
				newLandmarks.append(self.courseSegs[x].to_poi)
		self.reset(self.course, self.origin, self.destination, self.routeType, self.night, newLandmarks, self.cruising_alt, self.cruise_speed, self.climb_speed, self.climb_dist, self.gph, self.descent_speed, climb_done = True, doWeather = True)
		return 

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

# rounds to next thousand 
def roundthousand(num):
	return int(math.ceil(num/1000.0))*1000

def getProperAlt(origin, destination, course):
	start = str(origin.latlon)
	end = str(destination.latlon)
	path = start + "|" + end
	elevations = getElevation(path)
	# get the maximum altitude 
	maxAlt = max(elevations)
	# for hemispheric rule
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

	# elevrange = "-500,"+str(cruise_alt)
	pathMap = getChart(elevations)

	return (cruise_alt, pathMap)

def createRoute(home, dest, altitude, airspeed, custom=[], changed=False): 
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
	route = Route(course, origin, destination, routeType=rType, custom=custom, cruising_alt=final_alt, cruise_speed=airspeed, climb_speed=75, climb_dist=7, doWeather=False)

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
	
	# route path line 
	for item in route.courseSegs: 
		path.append((float(item.to_poi.lat), float(item.to_poi.lon)))
		mymap.addpoint(float(item.to_poi.lat), float(item.to_poi.lon))

	mymap.addpath(path,"#4169E1")

	return (getHtml(mymap), noTOC, route, elevation_map, messages)

# creates a static map for PDF viewing; should use url encoder
def makeStaticMap(segments,destination):
	# clip art: http://images.all-free-download.com/images/graphiclarge/silhouette_plane_clip_art_15576.jpg
	base_url = "https://maps.googleapis.com/maps/api/staticmap?&size=500x200&maptype=terrain" 
	num = 1 # number each label on map
	if len(segments) < 10: 
		for item in segments: 
			base_url += "&markers=color:blue%%7Clabel:%s%%7C%s,%s" % (num, item.from_poi.lat, item.from_poi.lon)
			num += 1
		base_url += "&markers=color:blue%%7Clabel:%s%%7C%s,%s" % (num, destination.lat, destination.lon)
	# add red path
	base_url += "&path=color:red%7Cweight:5%7C"
	for item in segments: 
		base_url +=  str(item.from_poi.lat) + "," + str(item.from_poi.lon) + "%7C"
	base_url += str(destination.lat) + "," + str(destination.lon)
	return base_url

# gets potential points of interest from a file 
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

# changes a particular landmark along a route and returns a new route
def changeRoute(r, n, p, home, dest, altitude, airspeed): # route, leg # to change, where to change it to 
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
	return createRoute(home, dest, altitude, airspeed, newLandmarks, True)

if __name__ == "__main__":
	# testing features 
	print 'start'
	home = "KHPN" 
	dest = "KGON"

	a = createRoute(home, dest, 1000, 110)
	print a[2].courseSegs
	num = "1"
	b = changeRoute(a[1], int(num), "New Haven", home, dest, 3500, 110)
	print b[1].courseSegs
	print b[2].courseSegs

	# print "Fuel required: " + str(route.fuelRequired)
	# print "Time required: " + str(route.time)
	# print "Route Distance: " + str(route.totalDist)
	# for item in courseSegs: 
	# print item.from_poi.lat, item.from_poi.lon