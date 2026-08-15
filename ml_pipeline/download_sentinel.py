import openeo
from datetime import datetime, timedelta

# 1. Establish the connection to the CDSE backend
connection = openeo.connect("openeo.dataspace.copernicus.eu")

# 2. Authenticate
# This will open a browser window for you to log in with your CDSE credentials
try:
    connection = connection.authenticate_oidc(
        max_poll_time=60, 
        display=True
    )
    print("✅ Authentication successful")
except Exception as e:
    print(f"Authentication failed: {e}")

# 3. Define the Spatial Extent (Bounding Box for your coastal area)
# Example coordinates for a coastal patch
spatial_extent = {
    "west": 82.20, 
    "east": 82.50, 
    "south": 16.80, 
    "north": 17.10
}

# 4. Define the Temporal Extent (Date Range)
# We will look for data from the past 3 months
today_date = datetime.now().date()
month_3_data = today_date - timedelta(days=(3*30))
temporal_extent = [str(month_3_data), str(today_date)]

print(f"Searching area: {spatial_extent}")
print(f"Time range: {temporal_extent}")

# 5. Build the Data Cube Request
# We are requesting Sentinel-2 Level-2A data (atmospherically corrected)
# We filter for images with less than 50% cloud cover
# We select only the bands necessary for marine debris detection
sentinel2_cube = connection.load_collection(
    "SENTINEL2_L2A", 
    spatial_extent=spatial_extent,
    temporal_extent=temporal_extent,
    bands=["B02", "B03", "B04", "B08", "B11"], 
    max_cloud_cover=50 
)

# 6. Process and Download
# Since we just want the raw data downloaded, we instruct the API to save it as a netCDF or GeoTIFF
# Note: Further temporal aggregation or cloud masking methods can be applied here before downloading
job = sentinel2_cube.execute_batch(
    output_format="NetCDF",
    title="Sentinel2_MarineDebris_Bands"
)

print(f"Job started! ID: {job.job_id}")
# You can use job.download_results("output_folder_path") once the job completes on the server.

# 7. Wait for the cloud processing job to finish
print("⏳ Waiting for Copernicus cloud server to process and package your images...")
job.start_and_wait()

# 8. Once finished, download the files directly to your local folder
print("⬇️ Downloading results to local folder...")
results = job.get_results()
results.download_files("datasets/sentinel_2/")

print("✅ Download complete! Check your sentinel_2 folder.")