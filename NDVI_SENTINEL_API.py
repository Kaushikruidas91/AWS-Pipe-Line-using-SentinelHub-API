# -*- coding: utf-8 -*-
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.plot import show
from sentinelsat import SentinelAPI
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from rasterio.mask import mask
from sklearn.linear_model import LinearRegression



# Parameters
USER = 'kaushikruidas@gmail.com' 
PASSWORD = 'Kaushik@91' 
REGION_FILE = 'C:/GrowIndigo/Kudhar_gp_UP.geojson'  
OUTPUT_DIR = 'C:/GrowIndigo/sentinel_data/'

# Using fixed dates (correctly formatted strings)
#START_DATE = '2024-06-01'
#END_DATE = '2024-11-30'

# OR using dynamic calculation (correct method)
START_DATE = (date.today() - timedelta(days=182)).strftime('2024-06-01')
END_DATE = date.today().strftime('2024-11-30')

CLOUD_COVER = 20  # Maximum cloud cover percentage
BANDS = {"B4": "B04.jp2", "B8": "B08.jp2", "B2": "B02.jp2"}  # Sentinel-2 bands for indices

# Connect to Sentinel API
api = SentinelAPI(USER, PASSWORD, 'https://apps.sentinel-hub.com/dashboard/#/configurations')

# Load region of interest
region = gpd.read_file(REGION_FILE)
geom = region.geometry.values[0]
bbox = region.total_bounds

# Search and download data
products = api.query(
    area=geom.wkt,
    date=(datetime.strptime(START_DATE, '2024-06-01'), datetime.strptime(END_DATE, '2024-11-30')), 
    cloudcoverpercentage=(20, CLOUD_COVER) 
)

# Print the results
print(f"Found {len(products)} products.")


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

downloaded_files = []
for product_id, product_info in products.items():
    api.download(product_id, OUTPUT_DIR)
    downloaded_files.append(product_info['title'])

# Process downloaded images
def calculate_indices(image_paths, mask_geom):
    indices = []
    for path in image_paths:
        with rasterio.open(os.path.join(path, BANDS['B4'])) as red, \
             rasterio.open(os.path.join(path, BANDS['B8'])) as nir, \
             rasterio.open(os.path.join(path, BANDS['B2'])) as blue:
            red_data = red.read(1).astype('float32')
            nir_data = nir.read(1).astype('float32')
            blue_data = blue.read(1).astype('float32')
            
            # Mask the bands
            if mask_geom:
                red_data, _ = mask(red, mask_geom, crop=True)
                nir_data, _ = mask(nir, mask_geom, crop=True)
                blue_data, _ = mask(blue, mask_geom, crop=True)
            
            # NDVI Calculation
            ndvi = (nir_data - red_data) / (nir_data + red_data + 1e-10)
            evi = 2.5 * ((nir_data - red_data) / (nir_data + 6 * red_data - 7.5 * blue_data + 1))

            # Collect statistics
            indices.append({
                "ndvi_mean": np.nanmean(ndvi),
                "evi_mean": np.nanmean(evi),
                "date": path.split('_')[-1][:8]
            })

    return indices

# Analyze vegetation indices
results = calculate_indices(downloaded_files, geom)

# Visualization
ndvi_series = [res['ndvi_mean'] for res in results]
evi_series = [res['evi_mean'] for res in results]
dates = [res['date'] for res in results]

plt.figure(figsize=(12, 6))
plt.plot(dates, ndvi_series, label='NDVI', color='green')
plt.plot(dates, evi_series, label='EVI', color='blue')
plt.xlabel('Date')
plt.ylabel('Index Value')
plt.title('Time-Series Vegetation Indices')
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'vegetation_indices.png'))
plt.show()

# Summary Report
report_content = f"""
Time-Series Analysis Report
===========================

Region: {REGION_FILE}
Start Date: {START_DATE}
End Date: {END_DATE}
Number of Images Processed: {len(downloaded_files)}

Key Statistics:
---------------
NDVI Mean: {np.nanmean(ndvi_series):.2f}
EVI Mean: {np.nanmean(evi_series):.2f}

A visualization of the time-series indices has been saved to {OUTPUT_DIR}.
"""

with open(os.path.join(OUTPUT_DIR, 'report.txt'), 'w') as report_file:
    report_file.write(report_content)

print(report_content)

