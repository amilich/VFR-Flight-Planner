f1 = open('cities.txt', 'w+')

with open("allCities.csv") as f:
	lines = f.readlines()
	for line in lines[1:]: 
		myLine = line.replace("\"", "")
		items = myLine.split(",")
		if(items[1].strip() == ""): 
			continue
		string = items[3] + " " + items[4] + ", " + items[1] + ", " + items[2] + "\n"
		f1.write(string)

# alreadyUsed = ""
# f2 = open('citiesFinal.txt', 'w+')

# with open("edited.txt") as f: 
# 	lines = f.readlines()
# 	for line in lines: 
# 		if line.split(", ")[0] not in alreadyUsed: 
# 			alreadyUsed += line.split(", ")[0] + " "
# 			f2.write(line)

# screwed up for towns with same name