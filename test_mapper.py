from gmplot_cust import *
import pygmaps

path = [(41.06695823, -73.7075749), (41.086709228, -73.6005218078), (41.143396, -73.289859), (41.26369858, -72.88680267), (41.298201, -72.532934), (41.33005578, -72.04513863), '#4169E1']
center = (41.26369858, -72.88680267)
zoom = 7

del path[-1]
lat = [float(x[0]) for x in path]
lon = [float(x[1]) for x in path]
print 'Creating gmaps plotter'
mapper = GoogleMapPlotter(center[0], center[1], zoom)
ll_path = lat + lon
ll_comb = [lat, lon]
mapper.plot(ll_comb[0], ll_comb[1], "plum", edge_width=10)
print mapper
print mapper.draw()