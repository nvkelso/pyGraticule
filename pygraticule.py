# By Alex Mandel Copyright 2012
# Modifications by Nathaniel Vaughn KELSO
#
# Script to generate a graticule that will reproject cleanly(smooth arcs) at world scale
# Output format is geojson, because it's easy to write as a text file python.
# Use ogr2ogr to convert to a SHP format "Esri Shapefile"
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys, math
import os, stat
from optparse import OptionParser

parser = OptionParser(usage="""%prog [options]

Generates a GeoJSON file with graticules spaced at specified interval.""")

parser.add_option('-g', '--grid_interval', dest='grid_interval', default=1.0, type='float',
                  help='Grid interval in decimal degrees, defaults to 1.')

parser.add_option('-t', '--grid_type', dest='grid_type', default="line",
                  help='Grid type, defaults to `line` (polyline), other values `rectangle` (polygon) and `hex` (polygon).')

parser.add_option('-s', '--step_interval', dest='step_interval', default=0.5, type='float',
                  help='Step interval in decimal degrees, defaults to 0.5.')

parser.add_option('-o', dest='outfilename', default='',
                  help='Output filename (with or without path), defaults to "graticule_1dd.geojson".')

parser.add_option('-f', dest='field_content', default='',
                  help='Add extra fields with default values to the output.')


def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


(options, args) = parser.parse_args()

#set the stepping of the increment, converting from string to interger
grid_accuracy = options.grid_interval
step_precision = options.step_interval
field_content_raw = options.field_content
grid_type = options.grid_type

if grid_type == 'line':
	polygonize = False
else:
	polygonize = True

if field_content_raw != ' ' and field_content_raw != '':
    field_content = ''',
                %s,''' % field_content_raw
else:
    field_content = ''

# destination file
out_file = options.outfilename
if out_file:
    # remember the directory that file is contained by
    out_dir = os.path.dirname( os.path.abspath(out_file) )
    out_name = os.path.basename( os.path.abspath(out_file) )
else:
    out_dir = 'output/'
    # destination file
    out_extension = 'geojson'
    # for the demo, we put the results in an "output dir for prettier results    
    out_name = ('graticule_%ddd') % (grid_accuracy)
    out_file = out_dir + out_name + '.' + out_extension

if polygonize:
    out_file_polygon = out_dir + out_name + '_polygon' + '.' + out_extension

# If the output directory doesn't exist, make it so we don't error later on file open()
if not os.path.exists(out_dir):
    print 'making dir...'
    os.makedirs(out_dir)

grid_file = open(out_file,"w")

# Stub out the GeoJSON format wrapper
header = ['{ "type": "FeatureCollection",','"features": [']
footer = [']','}']

grid_file.writelines(header)
    
# Create Geojson lines horizontal, latitude
for x in frange(-90,91,grid_accuracy):
    featstart = '''\n\t{ "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": ['''
    grid_file.write(featstart)
    for y in frange(-180,181,step_precision):
        if y == -180:
            grid_file.write("[")
        else:
            grid_file.write(",[")
        #print y,x
        grid_file.write(",".join([str(y),str(x)]))
        grid_file.write("]")
    # Figure out if it's North or South
    if x >= 0:
        direction = "N"
    else:
        direction = "S"
    label = " ".join([str(abs(x)),direction])
    featend = ''']},
      "properties": {
        "degrees": %d,
        "direction": "%s",
        "display":"%s",
        "dd":%d
        %s
        }
      },''' % (abs(x),direction,label,x, field_content)
    grid_file.write(featend)

# Create lines vertical, longitude
for y in frange(-180,181,grid_accuracy):
    featstart = '''\t{ "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": ['''
    grid_file.write(featstart)
    for x in frange(-90,91,step_precision):
        if x == -90:
            grid_file.write("[")
        else:
            grid_file.write(",[")
        #print y,x
        grid_file.write(",".join([str(y),str(x)]))
        grid_file.write("]")
        
    # Figure out if it's East or West
    if y >= 0:
        direction = "W"
    else:
        direction = "E"
    label = " ".join([str(abs(y)),direction])
    featend = ''']},
      "properties": {
        "degrees": %d,
        "direction": "%s",
        "display":"%s",
        "dd":%d
        %s
        }
      },\n''' % (abs(y),direction,label,y, field_content)
    grid_file.write(featend)

grid_file.writelines(footer)
grid_file.close()


if polygonize:
    polygon_file = open(out_file_polygon,"w")
    polygon_file.writelines(header)

    if grid_type == 'rectangle':
		
		# Create Geojson polygons
		for x in frange(-90,90,grid_accuracy):
			for y in frange(-180,180,grid_accuracy):
				featstart = '''\t{ "type": "Feature",
				  "geometry": {
					"type": "Polygon",
					"coordinates": [[['''
				polygon_file.write(featstart)
	
				#if y == -180:
				#    polygon_file.write("[")
				#else:
				#    polygon_file.write(",[")
				#print y,x
				#init upper left coord
				polygon_file.write(",".join([str(y),str(x)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y),str(x+grid_accuracy)]))
				polygon_file.write("],[")
				#lower right
				polygon_file.write(",".join([str(y+grid_accuracy),str(x+grid_accuracy)]))
				polygon_file.write("],[")
				#lower left
				polygon_file.write(",".join([str(y+grid_accuracy),str(x)]))
				polygon_file.write("],[")
				#back to close on init upper left coord
				polygon_file.write(",".join([str(y),str(x)]))
				polygon_file.write("]")
	
				# Figure out if it's North or South
				if x >= 0:
					direction_x = "N"
				else:
					direction_x = "S"
				if y >= 0:
					direction_y = "E"
				else:
					direction_y = "W"
				label = " ".join([str(abs(x)),direction_x,str(abs(y)),direction_y])
				label_x = " ".join([str(abs(x)),direction_x])
				label_y = " ".join([str(abs(y)),direction_y])
				featend = ''']]},
				  "properties": {
					"degree_x": %d,
					"direction_x": "%s",
					"display_x": "%s",
					"dd_x":%d,
					"degree_y": %d,
					"direction_y": "%s",
					"display_y": "%s",
					"dd_y": %d,
					"display": "%s"
					%s
					}
				  },\n''' % (abs(x),direction_x,label_x,x, abs(y),direction_y,label_y,y, label, field_content)
				
				polygon_file.write(featend)
			
    if grid_type == 'hex':
		vspacing = grid_accuracy
		originx = -90 - grid_accuracy / 2
		originy = -180 - grid_accuracy / 2
		width = 180 + grid_accuracy
		height = 360 + grid_accuracy
		#originx = -180
		#originy = -90
		#width = 360
		#height = 180
		
		# To preserve symmetry, hspacing is fixed relative to vspacing
		xvertexlo = 0.288675134594813 * vspacing;
		xvertexhi = 0.577350269189626 * vspacing;
		hspacing = xvertexlo + xvertexhi

		x = originx + xvertexhi
		# print str(x) + ", " + str(-180 + width)
		
		colnum = 0
		while x < (originx + width):
			if (colnum % 2) == 0:
				y = originy + (vspacing / 2.0)
			else:
				y = originy + vspacing

			# print str(x) + "," + str(y)

			while y < (originy + height):
				featstart = '''\t{ "type": "Feature",
						"geometry": {
						"type": "Polygon",
						"coordinates": [[['''
				polygon_file.write(featstart)

				polygon_file.write(",".join([str(y),str(x + xvertexhi)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y + (vspacing / 2.0)),str(x + xvertexlo)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y + (vspacing / 2.0)),str(x - xvertexlo)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y),str(x - xvertexhi)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y - (vspacing / 2.0)),str(x - xvertexlo)]))
				polygon_file.write("],[")
				#upper right
				polygon_file.write(",".join([str(y - (vspacing / 2.0)),str(x + xvertexlo)]))
				polygon_file.write("],[")
				#back to close on init upper left coord
				polygon_file.write(",".join([str(y),str(x + xvertexhi)]))
				polygon_file.write("]")

				#polyline = []
				#polyline.append([x + xvertexhi, y])
				#polyline.append([x + xvertexlo, y + (vspacing / 2.0)])
				#polyline.append([x - xvertexlo, y + (vspacing / 2.0)])
				#polyline.append([x - xvertexhi, y])
				#polyline.append([x - xvertexlo, y - (vspacing / 2.0)])
				#polyline.append([x + xvertexlo, y - (vspacing / 2.0)])
		
				#print polyline

				featend = ''']]},
				  "properties": { }
				  },\n'''
				
				polygon_file.write(featend)

				# add attributes
				# write to meta string (x, y)
				y = y + vspacing;

			x = x + hspacing
			colnum = colnum + 1
		
    polygon_file.writelines(footer)
    polygon_file.close()