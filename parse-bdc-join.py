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
import sys
try:
    import fiona
except ImportError:
    print("needs fiona - recommend sudo apt install python3-fiona or pip3 install fiona")
    sys.exit(1)

# To install/use this you will need to install the python3-fiona library
# sudo apt install -y python3-fiona

# parse the CostQuest BDC files for use later

# file format: (FCC_Active_BSL_12312022_ver1.csv)
# "location_id","address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude"
#
# file format: (FCC_Active_NoBSL_12312022_ver1.csv)
# "location_id","address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude"

# file format: (FCC_Secondary_12312022_ver1.csv)
# "location_id","address_id","parcel_id","address_confidence_code","address_range","pre_direction","street_name","suffix","post_direction","primary_secondary","address","city","state","zip","zip_suffix","address_source"
#
# file format: (FCC_Supplemental_06302026_rel_9.csv)
# "location_id","address_id","parcel_id","address_confidence_code","address_range","pre_direction","street_name","suffix","post_direction","primary_supplemental","address","city","state","zip","zip_suffix","address_source","fcc_rel"

location_info = { }

# unique list of all headers in file(s)
headers = ( "address_primary","city","state","zip","zip_suffix","unit_count","bsl_flag","building_type_code","land_use_code","address_confidence_code","county_geoid","block_geoid","h3_9","latitude","longitude","address_id","parcel_id","address_range","pre_direction","street_name","suffix","post_direction","primary_secondary","primary_supplemental","address","address_source","fcc_rel")

# names of your CQ BDC files you want to be processed
bdc_files = [ "FCC_Active_BSL_06302026_rel_9.csv", "FCC_Active_NoBSL_06302026_rel_9.csv", "FCC_Supplemental_06302026_rel_9.csv" ]


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def csv_dict_reader(csvfile):
    reader = csv.DictReader(csvfile)
    if reader.fieldnames:
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]
    return reader


# read the CQ BDC files
for read_file in bdc_files:
    print ("Starting to parse: %s" % read_file)
    with open(read_file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv_dict_reader(csvfile)
        for row in reader:
            location_id = row['location_id']
            if location_id not in location_info:
                location_info[location_id] = { 'source_file': [], 'provider_list': [], 'location_id': location_id }

            if read_file not in location_info[location_id]['source_file']:
                location_info[location_id]['source_file'].append(read_file)

            # populate the data from the CSV files into the location_info object
            for h in headers:
                if row.get(h, None) is not None:
                    location_info[location_id][h] = row[h]
            # newer CQ files renamed primary_secondary -> primary_supplemental
            if location_info[location_id].get('primary_secondary') is None and location_info[location_id].get('primary_supplemental') is not None:
                location_info[location_id]['primary_secondary'] = location_info[location_id]['primary_supplemental']

# bdc_26_Fiber-to-the-Premises_fixed_broadband_063022.csv
# frn,provider_id,brand_name,location_id,technology,max_advertised_download_speed,max_advertised_upload_speed,low_latency,business_residential_code,state_usps,block_geoid,h3_res8_id

bdc_26_headers = ('frn','provider_id','brand_name','location_id','technology','max_advertised_download_speed','max_advertised_upload_speed','low_latency','business_residential_code','state_usps','block_geoid','h3_res8_id')
# bdc 26 parser

bdc_skip_headers = ('location_id', 'state_usps', 'block_geoid')

# names of technology files from fcc.gov
# served/unserved summary files have no provider/speed columns and are skipped
technology_files = [
    "bdc_26_Cable_fixed_broadband_D25_15sep2026.csv",
    "bdc_26_FibertothePremises_fixed_broadband_D25_15sep2026.csv",
    "bdc_26_LBRFixedWireless_fixed_broadband_D25_15sep2026.csv",
    "bdc_26_LicensedFixedWireless_fixed_broadband_D25_15sep2026.csv",
    "bdc_26_NGSOSatellite_fixed_broadband_D25_15sep2026.csv",
]


# your output file name

fiona_outfile = 'bdc_20260630_15sep2026_results.shp'

for read_file in technology_files:
    print ("Starting to parse: %s" % read_file)
    with open(read_file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv_dict_reader(csvfile)
        for row in reader:
            # only populate location_ids we have the CQ files for
            if row.get('location_id') in location_info:
                temp_object = { }
                # build the object ouf of the bdc_26 file
                for h in bdc_26_headers:
                    if row.get(h, None) is not None:
                        # we do not need these headers as they are in the parent object
                        if h not in bdc_skip_headers:
                            temp_object[h] = row[h]
                # skip rows that have no advertised download speed to compare
                if not temp_object.get('max_advertised_download_speed'):
                    continue
                # add this provider to the list
                location_info[row['location_id']]['provider_list'].append(temp_object)

# schema for ESRI Shapefile
# Note they have a 10 char limit on colunm size (ugh)

schema = {
      'geometry': 'Point',
      'properties': {
          'name': 'str',
          'city': 'str',
          'state': 'str',
          'unit_count': 'int',
          'blk_geoid': 'str',
          'zip': 'str',
          'loc_id': 'str',
          'cnty_geoid': 'str',
          'src_file': 'str',
          'fast_isp': 'str',
          'speed_up': 'int',
          'speed_down': 'int',
          'technology': 'str',
      },
}

# iterate over each row in the source files
with fiona.open(fiona_outfile, mode='w', driver='ESRI Shapefile', schema = schema, crs = "EPSG:4326") as pointShp:
    for x in location_info:
#    if location_info[x].get('state', None) == 'OH':
        try:
            lon = float(location_info[x].get('longitude'))
            lat = float(location_info[x].get('latitude'))
        except (TypeError, ValueError):
            continue
        # create row that is written to shapefile
        rowDict = {
            'geometry' : {
                'type': 'Point',
                'coordinates': (lon, lat)
            },
            'properties': {
                'name' : location_info[x].get('address_primary', None),
                'city' : location_info[x].get('city', None),
                'state': location_info[x].get('state', None),
                'unit_count': safe_int(location_info[x].get('unit_count'), -1),
                'blk_geoid': location_info[x].get('block_geoid') or None,
                'zip': location_info[x].get('zip') or None,
                'loc_id': location_info[x].get('location_id') or None,
                'cnty_geoid': location_info[x].get('county_geoid') or None,
                'src_file': ','.join(location_info[x].get('source_file', [])),
                'fast_isp': None,
                'speed_up': -1,
                'speed_down': -1,
                'technology': None
            }
        }
        for pl in location_info[x]['provider_list']:
    #        print(pl)
            speed_down = safe_int(pl.get('max_advertised_download_speed'), -1)
            if speed_down > rowDict['properties']['speed_down']:
                rowDict['properties']['speed_down'] = speed_down
                rowDict['properties']['fast_isp'] = pl.get('brand_name')
                rowDict['properties']['speed_up'] = safe_int(pl.get('max_advertised_upload_speed'), -1)
                rowDict['properties']['technology'] = pl.get('technology')
    #        print('rowDict', rowDict)
#        if rowDict['properties'].get('technology', None) is not None:
        pointShp.write(rowDict)
#
print("wrote out %s" % fiona_outfile)
#
