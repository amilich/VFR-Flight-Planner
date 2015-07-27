import pygmaps

def getHtml(myMap): 
		string = "" 
		string += ('<div>\n')
		#string += ('<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />\n')
		#string += ('<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>\n')
		string += ('<script type="text/javascript" src="https://maps.google.com/maps/api/js?sensor=false"></script>\n')
		string += ('<script type="text/javascript">\n')
		string += ('\tfunction initialize() {\n')
		string += ('\t\tvar centerlatlng = new google.maps.LatLng(%f, %f);\n' % (myMap.center[0],myMap.center[1]))
		string += ('\t\tvar myOptions = {\n')
		string += ('\t\t\tzoom: %d,\n' % (myMap.zoom))
		string += ('\t\t\tcenter: centerlatlng,\n')
		string += ('\t\t\tmapTypeId: google.maps.MapTypeId.ROADMAP\n')
		string += ('\t\t};\n')
		string += ('\t\tvar map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);\n')
		string += ('\n')
		for point in  myMap.points:
			lat = point[0]
			lon = point[1]
			color = point[2]
			string += ('\t\tvar latlng = new google.maps.LatLng(%f, %f);\n'%(lat,lon))
			string += ('\t\tvar img = new google.maps.MarkerImage(\'%s\');\n' % (myMap.coloricon.replace('XXXXXX',color)))
			string += ('\t\tvar marker = new google.maps.Marker({\n')
			string += ('\t\ttitle: "no implimentation",\n')
			string += ('\t\ticon: img,\n')
			string += ('\t\tposition: latlng\n')
			string += ('\t\t});\n')
			string += ('\t\tmarker.setMap(map);\n')
			string += ('\n')

		clickable = False
		geodesic = True
		strokeColor = "#000000"
		strokeOpacity = 1.0
		strokeWeight = 2

		for path in myMap.paths:
			if(len(path) > 2): 
				strokeColor = "FF0000" # custom 
			#print path
			path = path[:-1]
			#strokeColor = path[-1]
			string += ('var PolylineCoordinates = [\n')
			for coordinate in path:
				string += ('new google.maps.LatLng(%s, %s),\n' % (coordinate[0],coordinate[1]))
			string += str('];\n')
			string += str('\n')

			string += ('var Path = new google.maps.Polyline({\n')
			string += ('clickable: %s,\n' % (str(clickable).lower()))
			string += ('geodesic: %s,\n' % (str(geodesic).lower()))
			string += ('path: PolylineCoordinates, \n')
			string += ('strokeColor: "' + str(strokeColor) + ' ",\n')
			string += ('strokeOpacity: ' + str(strokeOpacity) + ' ,\n')
			string += ('strokeWeight: ' + str(strokeWeight) + ' \n')
			string += ('});\n')
			string += ('\n')
			string += ('Path.setMap(map);\n')
			string += ('\n\n')

		string += ('\t}\n')
		string += ('</script>\n')
		string += ('</div>\n')
		string += ('<body style="margin:0px; padding:0px;" onload="initialize()">\n')
		string += ('\t<div id="map_canvas" style="width: 100%; height: 100%;"></div>\n')
		string += ('</body>\n') 

		return string