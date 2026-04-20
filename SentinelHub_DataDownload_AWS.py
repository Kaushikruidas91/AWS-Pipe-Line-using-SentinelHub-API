import boto3
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.plot import show
from rasterio.mask import mask
from shapely.geometry import box
from sentinelhub import WebFeatureService, BBox, CRS, DataCollection, SHConfig, MimeType, SentinelHubRequest, bbox_to_dimensions

# Define your AWS S3 configuration
aws_bucket = 'kaushik-aws'
aws_region = 'ap-south-1'

# Define your area of interest (AOI) using a shapefile
aoi_shapefile = 'D:/Kubota_Work/fatehbad_extent.shp'
aoi = gpd.read_file(aoi_shapefile)

# Extract the bounding box coordinates
aoi_bounds = aoi.total_bounds  # [min_x, min_y, max_x, max_y]
bbox = BBox(bbox=(aoi_bounds[0], aoi_bounds[1], aoi_bounds[2], aoi_bounds[3]), crs=CRS.WGS84)

# Calculate NDWI function
def calculate_ndwi(nir, green):
    ndwi = (green - nir) / (green + nir)
    return ndwi

# Function to download Sentinel-2 data and calculate NDWI
def download_and_calculate_ndwi(bbox, start_date, end_date):
    config = SHConfig()
    config.instance_id = 'cf5ffbdd-4c37-435c-b1c3-c16f7811aeca'
    config.sh_client_id = '908b9485-21c6-404e-a93a-f2722f1f0c6a'
    config.sh_client_secret = 'cGlORYUq7ar3MdXAtPEMla2LSUTHDIfp'
    
    # Request Sentinel-2 data
    wfs = WebFeatureService(
        bbox=bbox,
        time_interval=(start_date, end_date),
        data_collection=DataCollection.SENTINEL2_L1C,
        config=config
    )
    

    # Fetch available dates
    print(wfs,'wfswfswfs')
    print('1111111111111111=================')
    dates = wfs.get_dates()
    print(dates,'=================')
    if not dates:
        print('No data available for the given date range.')
        return

    # Download and process the data
    for date in dates:
         
        request = SentinelHubRequest(
            evalscript="""
                //VERSION=3
            
                function setup() {
                    return {
                        input: [{
                            bands: ["B03", "B08"]
                        }],
                        output: {
                            bands: 2
                        }
                    };
                }
            
                function evaluatePixel(sample) {
                    return [sample.B03, sample.B08];
                }
            """,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C,
                    time_interval=(date, date)
                )
            ],
            #print(input_data,'nxhjnxcdhjxc')
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=bbox_to_dimensions(bbox, resolution=10),
            config=config
        )
        print('till here')
        response = request.get_data(save_data=True)
        print(response,'responseresponse')
        green_band = response[0][:, :, 0]  # B03 corresponds to green band
        nir_band = response[0][:, :, 1]    # B08 corresponds to NIR band
        ndwi = calculate_ndwi(nir_band, green_band)

        # Save the NDWI result to a GeoTIFF file
        with rasterio.open(
                f'ndwi_{date}.tif',
                'w',
                driver='GTiff',
                height=ndwi.shape[0],
                width=ndwi.shape[1],
                count=1,
                dtype=ndwi.dtype,
                crs='EPSG:4326',
                transform=rasterio.transform.from_bounds(*aoi_bounds, ndwi.shape[1], ndwi.shape[0])
        ) as dst:
            dst.write(ndwi, 1)

        print(f'NDWI for {date} saved as ndwi_{date}.tif')

# Define your date range
start_date = '2017-01-01'
end_date = '2023-04-01'

# Run the download and NDWI calculation
download_and_calculate_ndwi(bbox, start_date, end_date)
