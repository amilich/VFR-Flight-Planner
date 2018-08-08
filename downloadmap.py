from flask_googlemaps import *

def getHtml3(malLL, landmarks, path, mymap):
	del path[-1]
	lat = [float(x[0]) for x in path]
	lon = [float(x[1]) for x in path]
	ll_path = lat + lon
	ll_comb = [lat, lon]
	marker_arr = []
	landmark_line_arr = []
	for lat, lon, landmark in zip(ll_comb[0], ll_comb[1], landmarks):
		marker_arr.append({
			 'icon': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
             'lat': lat,
             'lng': lon,
             'infobox': str(landmark.name)
		})
		landmark_line_arr.append({
			'lat': lat,
			'lng': lon,
		})
	route_polyline = {
        'stroke_color': '#ff00ff',
        'stroke_opacity': 1.0,
        'stroke_weight': 3,
        'path': landmark_line_arr,
    }
	print(landmark_line_arr)
	route_map = Map(
		style=(
            "height:100%;"
            "width:100%;"
        ),
		identifier="sndmap",
		lat=mymap.center[0],
		lng=mymap.center[1],
		markers=marker_arr,
		zoom=mymap.zoom,
		polylines=[route_polyline],
	)
	return route_map

