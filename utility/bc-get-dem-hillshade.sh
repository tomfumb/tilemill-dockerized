#!/bin/bash

DATA_DIR=./data/bc-dem
BASE_URL=https://pub.data.gov.bc.ca/datasets/175624/

mkdir -p $DATA_DIR
pushd $DATA_DIR

curl -s $BASE_URL | sed -rn 's/.*>([0-9]{2,3}[a-z])\/<.*/\1/p' | while read area
do
	curl -s $BASE_URL$area/ | sed -rn 's/.*>([0-9a-z_]+\.dem\.zip)<.*/\1/p' | while read file
	do
		wget $BASE_URL$area/$file
	done
	ls -1 *.zip | xargs -I{} unzip {}
	rm *.zip
done

$GDAL_SCRIPTS/gdal_merge.py -n -32767 -o bc-4269.dem `ls -1 *.dem | sed ':a;N;$!ba;s/\n/ /g'`
gdalwarp -s_srs EPSG:4269 -t_srs EPSG:3857 -r cubic bc-4269.dem bc-3857.dem
rm bc-4269.dem
gdaldem hillshade bc-3857.dem bc-hillshade-225-45.tiff -of GTiff -b 1 -z 1.0 -s 1.0 -az 225 -alt 45

popd