import simplejson
import urllib

# static elevation maps 
ELEVATION_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
CHART_BASE_URL = 'http://chart.googleapis.com/chart'

"""
See Google Maps API examples for Python. 

Constructs an elevation chart along a latitude and longitude path. 
"""
def getChart(chartData, chartDataScaling="-500,5000", chartType="lc",chartLabel="Elevation in Meters",chartSize="500x160", chartColor="orange", **chart_args):
    chart_args.update({
        'cht': chartType,
        'chs': chartSize,
        'chl': chartLabel,
        'chco': chartColor,
        'chds': chartDataScaling,
        'chxt': 'x,y',
        'chxr': '1,-500,5000'
    })
    dataString = 't:' + ','.join(str(x) for x in chartData)
    chart_args['chd'] = dataString.strip(',')
    chartUrl = CHART_BASE_URL + '?' + urllib.urlencode(chart_args)
    return chartUrl

"""
Gets elevation of a particular path with a particular number of samples. 
Used to construct elevation chart. 
"""
def getElevation(path,samples="75",sensor="false", **elvtn_args):
    elvtn_args.update({
        'path': path,
        'samples': samples,
        'sensor': sensor
    })

    url = ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args)
    response = simplejson.load(urllib.urlopen(url))
    elevationArray = []

    for resultset in response['results']:
      elevationArray.append(resultset['elevation'])

    return elevationArray