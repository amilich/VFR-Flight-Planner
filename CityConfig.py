# f1=open('us_cities.txt', 'w+')

# with open('cities.csv') as f:
#     content = f.readlines()
#     for line in content: 
#     	if "United States" in line: 
#     		f1.write(line)

import re as re

f1=open('newairports_2.txt', 'w+')
with open('ICAO_airports.csv') as f:
	content = f.readlines()
	for line in content: 
		if "US" in line and "small" not in line and "heli" not in line and "sea" not in line:
			data = line.replace("\"", "").split(",")
			for x in range(len(data)): 
				if("." in data[x] and not re.search("[a-zA-z]\.", data[x])): 
					f1.write(data[1] + ", " + data[x] + ", " + data[x+1] + "\n")
					break