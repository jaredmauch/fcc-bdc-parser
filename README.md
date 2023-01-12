# fcc-bdc-parser
FCC BDC Parser to Shapefile output

* This parses input files you receive from CQ, namely

```
FCC_Active_BSL_12312022_ver1.csv
FCC_Active_NoBSL_12312022_ver1.csv
FCC_Secondary_12312022_ver1.csv
```

and joins the data with the fixed broadband availability files available here:

https://broadbandmap.fcc.gov/data-download

You will need to download each of them and unzip them to the same director, eg:

```
bdc_26_Cable_fixed_broadband_063022.csv
bdc_26_Copper_fixed_broadband_063022.csv
bdc_26_Fiber-to-the-Premises_fixed_broadband_063022.csv
bdc_26_Licensed-Fixed-Wireless_fixed_broadband_063022.csv
bdc_26_NGSO-Satellite_fixed_broadband_063022.csv
bdc_26_Unlicensed-Fixed-Wireless_fixed_broadband_063022.csv
```

Once you have these, you can run the parser to generate your shapefile
dataset, eg:

`python3 parse-bdc-join.py`

The resulting output will look like this:

```
Starting to parse: FCC_Active_BSL_12312022_ver1.csv
Starting to parse: FCC_Active_NoBSL_12312022_ver1.csv
Starting to parse: FCC_Secondary_12312022_ver1.csv
Starting to parse: bdc_26_Cable_fixed_broadband_063022.csv
Starting to parse: bdc_26_Fiber-to-the-Premises_fixed_broadband_063022.csv
Starting to parse: bdc_26_NGSO-Satellite_fixed_broadband_063022.csv
Starting to parse: bdc_26_Copper_fixed_broadband_063022.csv
Starting to parse: bdc_26_Licensed-Fixed-Wireless_fixed_broadband_063022.csv
Starting to parse: bdc_26_Unlicensed-Fixed-Wireless_fixed_broadband_063022.csv
Unable to parse zipcode: *safe-to-ignore*
Unable to parse zipcode: *safe-to-ignore*
wrote out bdc_results.shp
```

please note you will want all the related shapefile extensions, the actual
list of files produced is:

```
bdc_results.cpg
bdc_results.dbf
bdc_results.prj
bdc_results.shp
bdc_results.shx
```

If you see any messages saying "Unable to parse zipcode" these are safe
to ignore.  The related data is shown, but the row will be written with
a NULL zipcode.

You should be able to modify the schema to add in other fields that are
not currently placed in the shapefile.  If you want to skip processing any
file, you can just remove it from the list, for example you can delete
Licensed-Fixed-Wireless or NGSO-Satellite list to eliminate those datasets
which may cause analysis related issues.

Good luck!
