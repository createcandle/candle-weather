# creates a library string for use in Python
import csv
import os

print("{")

with open('wmo_full_city_list.csv', 'r') as file:
    reader = csv.reader(file,delimiter=';')
    for each_row in reader:
        #print(each_row)
        #stringlist = each_row.split()
        #print(stringlist[1])
        
        print('"' + each_row[0] + " - " + each_row[1] + '": ' + each_row[2] + ',' )

print("}")