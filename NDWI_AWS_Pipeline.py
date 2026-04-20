import boto3
import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from rasterio.plot import show
from rasterio.mask import mask
from shapely.geometry import box

### SentinelHub Configure libraries #########
import matplotlib.pyplot as plt
import pandas as pd
import getpass

from sentinelhub import (
    SHConfig,
    DataCollection,
    SentinelHubCatalog,
    SentinelHubRequest,
    SentinelHubStatistical,
    BBox,
    bbox_to_dimensions,
    CRS,
    MimeType,
    Geometry,
)

#from utils import plot_image

# Define your AWS S3 configuration
aws_bucket = 'kaushik-aws'
aws_region = 'ap-south-1'

### SentinelHub Configuration #######
config = SHConfig()
config.sh_client_id = getpass.getpass("Enter your SentinelHub client id")
config.sh_client_secret = getpass.getpass("Enter your SentinelHub client secret")
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
config.sh_base_url = "https://sh.dataspace.copernicus.eu"
config.save("cdse")

# load area of interest (AOI) using a shapefile
aoi_shapefile = 'D:/Kubota_Work/fatehbad_extent.shp'
aoi = gpd.read_file(aoi_shapefile)

## Convert shp file as WGS84 and giving the Latitude and Longitude ######
aoi_coords_wgs84 = [75.4431, 29.4095, 75.5321, 29.4959]

resolution = 10
aoi_bbox = BBox(bbox=aoi_coords_wgs84, crs=CRS.WGS84)
aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)

print(f"Image shape at {resolution} m resolution: {aoi_size} pixels")

###### Catalog configuration #######
#### To show the total Number of Image Collection from the Dates
catalog = SentinelHubCatalog(config=config)
aoi_bbox = BBox(bbox=aoi_coords_wgs84, crs=CRS.WGS84)
time_interval = "2023-01-01", "2023-03-31"

search_iterator = catalog.search(
    DataCollection.SENTINEL2_L2A,
    bbox=aoi_bbox,
    time=time_interval,
    fields={"include": ["id", "properties.datetime"], "exclude": []},
)

results = list(search_iterator)
print("Total number of results:", len(results))

results

evalscript_true_color = """
    //VERSION=3

    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04"]
            }],
            output: {
                bands: 3
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B03, sample.B02];
    }
"""

request_true_color = SentinelHubRequest(
    evalscript=evalscript_true_color,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A.define_from(
                name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
            ),
            time_interval=("2023-01-01", "2023-01-31"),
            other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=aoi_bbox,
    size=aoi_size,
    config=config,
)

true_color_imgs = request_true_color.get_data()

print(
    f"Returned data type = {type(true_color_imgs)} and length {len(true_color_imgs)}."
)
print(
    f"Single element in the list is of type {type(true_color_imgs[-1])} and has shape {true_color_imgs[-1].shape}"
)

######### RGB IMAGE SHOW ##########
image = true_color_imgs[0]
print(f"Image type: {image.dtype}")

# plot RGB IMAGE PLOT
fig, ax=plt.subplots(figsize=(10,10))
plot = ax.imshow(image);
fig.colorbar(plot, ax=ax)
plt.show
#factor 1/255 to scale between 0-1
#factor 3.5 to increase brightness

##########   1. Extract Sentinel -2 data for the farm extent covering a certain time period #######
#########  For this extraction kindly use Sentinel 2 from public AWS S3 bucket ###############

######## NDWI GENERATION ###########
evalscript_ndvi = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "B03",
        "B08",
        "dataMask"
      ]
    }],
    output: {
      bands: 4
    }
  }
}
  

function evaluatePixel(sample) {
    let val = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
    let imgVals = null;
    
    if (val<-1.1) imgVals = [0,0,0];
    else if (val<-0.2) imgVals = [0.75,0.75,0.75];
    else if (val<-0.1) imgVals = [0.86,0.86,0.86];
    else if (val<0) imgVals = [1,1,0.88];
    else if (val<0.025) imgVals = [1,0.98,0.8];
    else if (val<0.05) imgVals = [0.93,0.91,0.71];
    else if (val<0.075) imgVals = [0.87,0.85,0.61];
    else if (val<0.1) imgVals = [0.8,0.78,0.51];
    else if (val<0.125) imgVals = [0.74,0.72,0.42];
    else if (val<0.15) imgVals = [0.69,0.76,0.38];
    else if (val<0.175) imgVals = [0.64,0.8,0.35];
    else if (val<0.2) imgVals = [0.57,0.75,0.32];
    else if (val<0.25) imgVals = [0.5,0.7,0.28];
    else if (val<0.3) imgVals = [0.44,0.64,0.25];
    else if (val<0.35) imgVals = [0.38,0.59,0.21];
    else if (val<0.4) imgVals = [0.31,0.54,0.18];
    else if (val<0.45) imgVals = [0.25,0.49,0.14];
    else if (val<0.5) imgVals = [0.19,0.43,0.11];
    else if (val<0.55) imgVals = [0.13,0.38,0.07];
    else if (val<0.6) imgVals = [0.06,0.33,0.04];
    else imgVals = [0,0.27,0];
    
    
    imgVals.push(sample.dataMask)
    
    return imgVals
}
"""

request_ndwi_img = SentinelHubRequest(
    evalscript=evalscript_ndvi,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A.define_from(
                name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
            ),
            time_interval=("2022-01-01", "2022-01-31"),
            other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=aoi_bbox,
    size=aoi_size,
    config=config,
)

ndwi_img = request_ndwi_img.get_data()

print(
    f"Returned data type is {type(true_color_imgs)} and length {len(true_color_imgs)}."
)
print(
    f"Single element in the list is of type {type(true_color_imgs[-1])} and has shape {true_color_imgs[-1].shape}"
)

##### NDWI Image PLOT ###########
image_NDWI = ndwi_img[0]
print(f"Image type: {image.dtype}")

# plot function
fig, ax=plt.subplots(figsize=(12,10))
plot = ax.imshow(image_NDWI);
fig.colorbar(plot, ax=ax)
plt.show


### To save data #####
## Define output file path
output_path = "D:/Kubota_Work/NDWI_jan_2023.tif"

# Save the NDVI result as a new TIFF file
with rasterio.open(
    output_path,
    'w',
    driver='GTiff',
    height=image_NDWI.shape[0],
    width=image_NDWI.shape[1],
    count=1,
    dtype=image_NDWI.dtype,
) as dst:
    dst.write(image_NDWI, 1)

print(f"NDVI image saved to {output_path}")

############# 2. Generate NDWI for the images ##########
##################################################

evalscript = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "B03",
        "B08",
        "dataMask"
      ]
    }],
    output: [
      {
        id: "ndwi",
        bands: 1
      },
      {
        id: "dataMask",
        bands: 1
      }]
  };
}

function evaluatePixel(samples) {
    let index = (samples.B08 - samples.B03) / (samples.B08+samples.B03);
    return {
        ndwi: [index],
        dataMask: [samples.dataMask],
    };
}

"""

######### Putting Two Different Polygon ###########
from shapely.geometry import Polygon
gdf = gpd.read_file("D:/Kubota_Work/Agri.shp")
gdf.crs

# give it in EPSG:4326 (WGS84)
gdf = gdf.to_crs(epsg=4326)

# Function to extract coordinates from the Polygon
def extract_coordinates(geometry):
    if isinstance(geometry, Polygon):
        return list(geometry.exterior.coords)
    else:
        raise ValueError("Geometry is not a Polygon")

# extract coordinates for each polygon in the GeoDataFrame
coordinates_list = gdf.geometry.apply(extract_coordinates).iloc[0]

# Print the extracted coordinates
for coord in coordinates_list:
    print(coord)

#### putting the coordinate value to the lists ###########
field1 = {
    "type": "Polygon",
    "coordinates": [
        [
            [75.48105438434891, 29.468790449923087],
            [75.49390958236091, 29.46898533602662],
            [75.49438925392855, 29.457987605878852],
            [75.48111834055791, 29.458460950467842],
            [75.48105438434891, 29.468790449923087],
            
        ]
    ],
} 


########### Use the Geometry ##############
geometry = Geometry(geometry=field1, crs=CRS.WGS84)

request = SentinelHubStatistical(
    aggregation=SentinelHubStatistical.aggregation(
        evalscript=evalscript,
        time_interval=("2023-06-01T00:00:00Z", "2023-12-30T23:59:59Z"),
        aggregation_interval="P10D",
        size=[368.043, 834.345],
    ),
    input_data=[
        SentinelHubStatistical.input_data(
            DataCollection.SENTINEL2_L1C.define_from(
                name="s2l1c", service_url="https://sh.dataspace.copernicus.eu"
            ),
            other_args={"dataFilter": {"maxCloudCoverage": 10}},
        ),
    ],
    geometry=geometry,
    config=config,
)

response1 = request.get_data()
response1


# define functions to extract Statistic for all the download  dates

def extract_stats(date, stat_data):
    d = {}
    for key, value in stat_data["outputs"].items():
        stats = value["bands"]["B0"]["stats"]
        if stats["sampleCount"] == stats["noDataCount"]:
            continue
        else:
            d["date"] = [date]
            for stat_name, stat_value in stats.items():
                if stat_name == "sampleCount" or stat_name == "noDataCount":
                    continue
                else:
                    d[f"{key}_{stat_name}"] = [stat_value]
    return pd.DataFrame(d)


def read_acquisitions_stats(stat_data):
    df_li = []
    for aq in stat_data:
        date = aq["interval"]["from"][:10]
        df_li.append(extract_stats(date, aq))
    return pd.concat(df_li)

##### To sea the results #########
result_data = read_acquisitions_stats(response1[0]["data"])
result_data


######## Plot the NDWI Profile According to their Accusigation date #########
fig_stat, ax_stat = plt.subplots(1, 1, figsize=(12, 6))
t1 = result_data["date"]
ndwi_mean_field1 = result_data["ndwi_mean"]
ndwi_std_field1 = result_data["ndwi_stDev"]
ax_stat.plot(t1, ndwi_mean_field1, label="field 1 mean")
ax_stat.fill_between(
    t1,
    ndwi_mean_field1 - ndwi_std_field1,
    ndwi_mean_field1 + ndwi_std_field1,
    alpha=0.3,
    label="field 1 stDev",
)
ax_stat.tick_params(axis="x", labelrotation=30, labelsize=12)
ax_stat.tick_params(axis="y", labelsize=12)
ax_stat.set_xlabel("Date", size=15)
ax_stat.set_ylabel("NDWI/unitless", size=15)
ax_stat.legend(loc="lower right", prop={"size": 12})
ax_stat.set_title("NDWI time series", fontsize=20)
for label in ax_stat.get_xticklabels()[1::2]:
    label.set_visible(False)

####### SAVE THE PROFILE TO THE DESTINATION #######
####### Save the line graph #####
plt.savefig("D:/Kubota_Work/NDWI_Time_Series.png")
plt.show()



##### Upload output files to the Buckets #######
##################
import boto3
import os


aws_bucket = 'kaushik-aws'
aws_region = 'ap-south-1'

#Create an S3 client
s3_client = boto3.client('s3', region_name=aws_region)

# Define a function to upload files to S3
def upload_to_s3(local_file_path, s3_bucket, s3_key):
    try:
        s3_client.upload_file(local_file_path, s3_bucket, s3_key)
        print(f"Successfully {local_file_path} to {s3_bucket}/{s3_key}")
    except Exception as e:
        print(f"Failed {local_file_path} to {s3_bucket}/{s3_key}")
        print(e)

#Upload the NDWI image and time series plot to S3
ndwi_image_path = "D:/Kubota_Work/NDWI_jan_2023.tif"
time_series_plot_path = "D:/Kubota_Work/NDWI_Time_Series.png"

# Upload the NDWI image
upload_to_s3(ndwi_image_path, aws_bucket, "NDWI/NDWI_jan_2023.tif")

# Upload the time series plot
upload_to_s3(time_series_plot_path, aws_bucket, "NDWI/NDWI_Time_Series.png")



