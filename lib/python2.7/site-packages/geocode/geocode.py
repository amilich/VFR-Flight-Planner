import os
import urllib
import cPickle as pickle
import json
import time


class NoResultError(Exception): pass
class QueryLimitError(Exception): pass

last_read = time.time()

try:
    pickle_dir = os.path.expanduser('~/.geocode/')
    os.makedirs(pickle_dir)
except:
    pickle_dir = './'

pickle_path = os.path.join(pickle_dir, 'latlons.pkl')

try:
    with open(pickle_path) as pkl_file:
        _latlons = pickle.load(pkl_file)
except: _latlons = {}


def save_cache():
    with open(pickle_path, 'w') as pkl_file:
        pickle.dump(_latlons, pkl_file, -1)


def latlon(location, throttle=0.5, center=True, round_digits=2):
    '''Look up the latitude/longitude coordinates of a given location using the
    Google Maps API. The result is cached to avoid redundant API requests.
    
    throttle: send at most one request in this many seconds
    center: return the center of the region; if False, returns the region
            (lat1, lon1, lat2, lon2)
    round_digits: round coordinates to this many digits
    '''

    global last_read

    if isinstance(location, list):
        return map(lambda x: latlon(x, throttle=throttle, center=center, round_digits=round_digits),
                   location)

    if location in _latlons:
        result = _latlons[location]
        if center:
            lat1, lon1, lat2, lon2 = result
            result = (lat1+lat2)/2, (lon1+lon2)/2
        return tuple([round(n) for n in result])

    while time.time() - last_read < throttle:
        pass
    last_read = time.time()

    try:
        url = "http://maps.google.com/maps/api/geocode/json?address=%s&sensor=false" % location.replace(' ', '+')
        data = json.loads(urllib.urlopen(url).read())
        if data['status'] == 'OVER_QUERY_LIMIT':
            raise QueryLimitError('Google Maps API query limit exceeded. (Use the throttle keyword to control the request rate.')
            
        try:
            bounds = data['results'][0]['geometry']['bounds']
            result1 = bounds['northeast']
            lat1, lon1 = result1['lat'], result1['lng']
            result2 = bounds['southwest']
            lat2, lon2 = result2['lat'], result2['lng']        
        except KeyError:
            bounds = data['results'][0]['geometry']['location']
            lat1 = bounds['lat']
            lon1 = bounds['lng']
            lat2 = lat1
            lon2 = lon1
        except IndexError:
            raise NoResultError('No result was found for location %s' % location)

        _latlons[location] = (lat1, lon1, lat2, lon2)
        save_cache()

        if center: return round((lat1+lat2)/2, round_digits), round((lon1+lon2)/2, round_digits)
        else: return tuple([round(n, round_digits) for n in (lat1, lon1, lat2, lon2)])
        
    except Exception as e:
        raise
        return None



if __name__ == '__main__':
    input = True

    while input:
        input = raw_input('Enter the name of a location: ')
        print latlon(input)