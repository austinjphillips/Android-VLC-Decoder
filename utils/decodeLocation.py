# -*- coding: utf-8 -*-
import re
import urllib.request

x = 210

url = "https://esviewer.tudelft.nl/space/" + str( x ) + "/"

print( "url: " +  url + "\n\n" )

with urllib.request.urlopen( url ) as f:
    html_code = f.read().decode( 'utf-8' )

# Define a regular expression pattern to match the title tag
title_pattern_hall = r'<title>(.*?)</title>'
pattern_building = r'<font size="5">(.*?)</font>'

pattern_hall  = re.compile( title_pattern_hall )
pattern_building  = re.compile( pattern_building )

# Use re.search to find the title within the HTML code
hall = re.search( pattern_hall, html_code )
building = re.search( pattern_building, html_code )

if hall:
    # Extract the title content from the match object
    hall = hall.group(1)
    print( "Hall:", hall )
else:
    print("Hall not found in the HTML code")
    
if building:
    # Extract the title content from the match object
    building = building.group(1)
    print( "Building:", building )
else:
    print("Building not found in the HTML code")
