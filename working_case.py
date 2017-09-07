#-*- coding: utf-8 -*-
import flickrapi
import sys
import codecs
from osgeo import ogr

#sys.argv[1] --> extent of searched area as shapefile 
#sys.argv[2] --> destination of created output as csv
try:
    infile_shape = sys.argv[1]	
    outfile_csv = sys.argv[2]
    
except:
	print "USAGE of this script: Shapefile_of_Bounding_Box.shp Output.csv"
	sys.exit()
 
drv = ogr.GetDriverByName('ESRI Shapefile')
ds_in = drv.Open(infile_shape)
lyr_in = ds_in.GetLayer(0)
extent = lyr_in.GetExtent()

#definition of bounding box of shapefile (min Longitude, min Latitude, max Longitude, max Latitude) 
shapebbox = "%s,%s,%s,%s" % (str(extent[0]),str(extent[2]),str(extent[1]),str(extent[3]))

#My data application:
api_key = "8f8fa0028f7f7dc6d7b1d21fc173c98b"
secret_api_key = "61f983a5fdc9a43e"

#create an API object:
flickr = flickrapi.FlickrAPI(api_key, secret_api_key)

#Search photos from a BBox:
#Documentation at https://www.flickr.com/services/api/flickr.photos.search.html
#for flood search enter in tags: "flood,Flut,Überschwemmung, Flood, Hochwasser, floodplain"
photo_list = flickr.photos.search(api_key=api_key, tags="flood,Flut,Überschwemmung, Flood, Hochwasser, floodplain", min_taken_date='2007-01-01 00:00:01', bbox=shapebbox, accuracy=16,
                                  content_type=7, has_geo=1, extras="description, license, date_upload, date_taken, owner_name, icon_server, original_format, last_update, tags, geo, machine_tags, o_dims, views, media, path_alias, url_sq, url_t, url_s, url_q, url_m, url_n, url_z, url_c, url_l, url_o",
                                  per_page=500,format='parsed-json')


pages = int(photo_list["photos"]["pages"])

#write outfile
outFile = codecs.open(outfile_csv, "w", "utf-8")
header = "fid;uid;tags;date;lat;lon;url\n"
outFile.write(header)


cnt_source = 0
cnt_final = 0

#write urls in set --> only distinct values --> no redundancy
uniqueurl = set()

for i in range(1, pages+1):
    for photo in photo_list["photos"]["photo"]:
        cnt_source+=1
        #get image content
        fid = int(photo["id"])
        uid = photo["owner"]
        lat = photo["latitude"]
        lon = photo["longitude"]
        #SetPoint_2D method needs float values
        floatlat = float(lat)
        floatlon = float(lon)
        
        if "tags" in photo:
            tags = photo["tags"]
        else:
            tags = ""

        if "datetaken" in photo:
            date = photo["datetaken"]
        else:
            date = ""
            
        #url_o = original image size --> best quality    
        if "url_o" in photo:
            url = photo["url_o"]
        #url_l --> next best image size (1024px on longest side)    
        elif "url_o" not in photo and "url_l" in photo:
            url = photo["url_l"]
        #url_c --> next best image size (800px on longest side) 
        elif "url_o" and "url_l" not in photo and "url_c" in photo:
            url = photo["url_c"]
        else:
            url = ""
        
        point = ogr.Geometry(ogr.wkbPoint)
        #create a temporary point from latlon
        point.SetPoint_2D(0, floatlon, floatlat)
        #set spatialfilter --> shapefile vs point
        lyr_in.SetSpatialFilter(point)
        
        #if point inside shapefile
        for feat_in in lyr_in:
            #only write an image ONCE in output --> otherwise duplicates when more than one keyword fits
            if url not in uniqueurl:
                cnt_final +=1            
                add = "%s;%s;%s;%s;%s;%s;%s\n" % (fid, uid, tags, date, lat, lon, url)
                outFile.write(add)
                uniqueurl.add(url)
            

print "Points in Bounding Box of Polygon:",cnt_source
print "Points in exact contour of Polygon:", cnt_final
outFile.close()
