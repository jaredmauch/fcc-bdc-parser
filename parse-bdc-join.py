#!/usr/bin/python3

# (c) 2023 - Jared Mauch
# 
# Parse the FCC provided BDC files and join them with the CQ BDC files that are available for
# filers in the FCC BDC system and output a resulting shapefile for use in another tool
# like qgis or similar
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
# 

import csv
#import geojson
#from geojson import Feature, Point, FeatureCollection
import fiona

# To install/use this you will need to install the python3-fiona library
# sudo apt install -y python3-fiona 
# You may uncomment the geojson code as well, if so you will need this:
# sudo apt install -y python3-geojson

# parse the CostQuest BDC files for use later

# file format: (FCC_Active_BSL_12312022_ver1.csv)
# "location_id","address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude"
#
# file format: (FCC_Active_NoBSL_12312022_ver1.csv)
# "location_id","address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude"

# file format: (FCC_Secondary_12312022_ver1.csv)
# "location_id","address_id","parcel_id","address_confidence_code","address_range","pre_direction","street_name","suffix","post_direction","primary_secondary","address","city","state","zip","zip_suffix","address_source"

location_info = { }

# unique list of all headers in file(s)
headers = ( "address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude","address_id","parcel_id","address_confidence_code","address_range","pre_direction","street_name","suffix","post_direction","primary_secondary","address","address_source")

# names of your CQ BDC files you want to be processed
files = ("FCC_Active_BSL_12312022_ver1.csv",
        "FCC_Active_NoBSL_12312022_ver1.csv",
        "FCC_Secondary_12312022_ver1.csv")

# read the CQ BDC files
for read_file in files:
    print ("Starting to parse: %s" % read_file)
    with open(read_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if location_info.get(row['location_id'], None) is None:
                location_info[row['location_id']] = { 'source_file': [], 'provider_list': [] }
                location_info[row['location_id']]['source_file'].append(read_file)
                location_info[row['location_id']]['location_id'] = row['location_id']

            # populate the data from the CSV files into the location_info object
            for h in headers:
                if row.get(h, None) is not None:
                    location_info[row['location_id']][h] = row[h]

# bdc_26_Fiber-to-the-Premises_fixed_broadband_063022.csv
# frn,provider_id,brand_name,location_id,technology,max_advertised_download_speed,max_advertised_upload_speed,low_latency,business_residential_code,state_usps,block_geoid,h3_res8_id

bdc_26_headers = ('frn','provider_id','brand_name','location_id','technology','max_advertised_download_speed','max_advertised_upload_speed','low_latency','business_residential_code','state_usps','block_geoid','h3_res8_id')
# bdc 26 parser

bdc_skip_headers = ('location_id', 'state_usps', 'block_geoid')

files = [ 'bdc_26_Cable_fixed_broadband_063022.csv', 'bdc_26_Fiber-to-the-Premises_fixed_broadband_063022.csv','bdc_26_NGSO-Satellite_fixed_broadband_063022.csv',
    'bdc_26_Copper_fixed_broadband_063022.csv', 'bdc_26_Licensed-Fixed-Wireless_fixed_broadband_063022.csv', 'bdc_26_Unlicensed-Fixed-Wireless_fixed_broadband_063022.csv' ]

for read_file in files:
    print ("Starting to parse: %s" % read_file)
    with open(read_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # only populate location_ids we have the CQ files for
            if location_info.get(row['location_id'], None) is not None:
                temp_object = { }
                # build the object ouf of the bdc_26 file
                for h in bdc_26_headers:
                    if row.get(h, None) is not None:
                        # we do not need these headers as they are in the parent object
                        if h not in bdc_skip_headers:
                            temp_object[h] = row[h]
                # add this provider to the list
                location_info[row['location_id']]['provider_list'].append(temp_object)

## print("Parsing into GeoJson")
## geo_features = [ ]
## for x in location_info:
##     if location_info[x]['zip'] in ('48103', '48130', '48118', '48158'):
##         myGeoPoint = Point((float(location_info[x]['latitude']), float(location_info[x]['longitude'])))
##         myGeoFeature = Feature(myGeoPoint)
##         myGeoFeature['properties'] = location_info[x]
##         geo_features.append(myGeoFeature)
## #        print(x,location_info[x])
## feature_collection = FeatureCollection(geo_features)
##
## print("Writing to myfie.geojson")
## count = 0
## with open('myfile.geojson', 'w') as f:
##     count = count + 1
##     geojson.dump(feature_collection, f, sort_keys=True, indent=4)
## print("Wrote %d entries to myfile.geojson" % count)

# schema for ESRI Shapefile
# Note they have a 10 char limit on colunm size (ugh)

schema = {
      'geometry': 'Point',
      'properties': {
          'name': 'str',
          'city': 'str',
          'state': 'str',
          'unit_count': 'int',
          'blk_geoid': 'int',
          'zip': 'int',
          'loc_id': 'int',
          'cnty_geoid': 'int',
          'src_file': 'str',
          'fast_isp': 'str',
          'speed_up': 'int',
          'speed_down': 'int',
          'technology': 'str',
      },
}

pointShp = fiona.open('bdc_results.shp', mode='w', driver='ESRI Shapefile', schema = schema, crs = "EPSG:4326")

# iterate over each row in the source files
for x in location_info:
    try:
        zipcode = int(location_info[x]['zip'])
    except:
        zipcode = None
        print("Unable to parse zipcode:", location_info[x])
    # create row that is written to shapefile
    rowDict = {
        'geometry' : {
            'type': 'Point',
            'coordinates': (float(location_info[x]['longitude']), float(location_info[x]['latitude']))
        },
        'properties': {
            'name' : location_info[x]['address_primary'],
            'city' : location_info[x]['city'],
            'state': location_info[x]['state'],
            'unit_count': int(location_info[x]['unit_count']),
            'blk_geoid': int(location_info[x]['block_geoid']),
            'zip': zipcode,
            'loc_id': int(location_info[x]['location_id']),
            'cnty_geoid': int(location_info[x]['county_geoid']),
            'src_file': ','.join(location_info[x]['source_file']),
            'fast_isp': None,
            'speed_up': -1,
            'speed_down': -1,
            'technology': None
        }
    }
    for pl in location_info[x]['provider_list']:
#        print(pl)
        if int(pl['max_advertised_download_speed']) > rowDict['properties']['speed_down']:
            rowDict['properties']['speed_down'] = int(pl['max_advertised_download_speed'])
            rowDict['properties']['fast_isp'] = pl['brand_name']
            rowDict['properties']['speed_up'] = int(pl['max_advertised_upload_speed'])
            rowDict['properties']['technology'] = pl['technology']
#        print('rowDict', rowDict)
    pointShp.write(rowDict)
#close fiona object
pointShp.close()
#
print("wrote out bdc_results.shp")
#
