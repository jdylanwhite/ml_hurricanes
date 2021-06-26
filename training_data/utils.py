import os
import urllib
import pandas as pd
import datetime
import xarray as xr
import requests
import netCDF4
import boto3

def download_ibtracs(basin="NA",dataDir="./data/",overwrite=True):

    """Download IBTrACS data from desired basin"""

    # Set the URL
    url = 'https://www.ncei.noaa.gov/data/'+\
          'international-best-track-archive-for-climate-stewardship-ibtracs/'+\
          'v04r00/access/csv/ibtracs.'+basin+'.list.v04r00.csv'

    # Set the file path
    filePath = dataDir+'ibtracs_'+basin+'.csv'

    # Download the file if it doesn't already exists
    if overwrite or not os.path.exists(filePath):
            urllib.request.urlretrieve(url,filePath)

    return filePath

def read_ibtracs(filePath,subsetSeason=False,yearStart=0,yearEnd=3000):

    """Read IBTrACS data to a pandas data frame, subset seasons if needed"""

    # Read the data from the CSV
    df = pd.read_csv(filePath,low_memory=False,skiprows=range(1,2))

    # Only keep a handful of columns
    keepColumns = ['SID','SEASON','NUMBER','NAME','ISO_TIME',
                'NATURE','LAT','LON','WMO_WIND','WMO_PRES','TRACK_TYPE',
                'DIST2LAND','LANDFALL','IFLAG','STORM_SPEED','STORM_DIR']
    df = df[keepColumns]

    # Convert time strings to datetimes for better querying
    df['ISO_TIME'] = pd.to_datetime(df['ISO_TIME'])
    df['SEASON'] = pd.to_numeric(df['SEASON'])
    df['NUMBER'] = pd.to_numeric(df['NUMBER'])
    df['LAT'] = pd.to_numeric(df['LAT'])
    df['LON'] = pd.to_numeric(df['LON'])

    # Subset seasons
    if subsetSeason:
        df = df[(df['SEASON'] >= yearStart) & (df['SEASON'] <= yearEnd)]

    return df

def day_of_year(date):

    """Take a datetime date and get the number of days since Jan 1 of that same year"""
    
    year = date.year
    firstDay = datetime.datetime(year,1,1)
    return (date-firstDay).days+1

def read_aws_creds():

    """Read AWS credentials stored at ~/rootkey.csv"""

    home = os.path.expanduser('~')
    awsCredPath = home+'/rootkey.csv'
    with open(awsCredPath,'r') as f:
        creds = f.read()

    return [cred.split('=')[1] for cred in creds.split('\n')]

def get_s3_keys(bucket, s3Client, prefix = ''):

    """Generate the keys in an S3 bucket."""
    
    # Build arguments dictionary
    kwargs = {'Bucket': bucket}
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix

    while True:

        resp = s3Client.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            key = obj['Key']
            if key.startswith(prefix):
                yield key

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

def get_goes16(date,product='ABI-L1b-RadF',band=3):

    """Retrieve GOES 16 full-disc image from AWS storage"""

    # Set image specific parameters
    bucketName = 'noaa-goes16'

    # Set date of image
    year = date.year
    day = day_of_year(date)
    hour = date.hour

    # Identify scan mode based on date
    if date < datetime.datetime(2019,4,2,16):
        scanMode = "M3"
    else:
        scanMode = "M6"

    # Initialize S3 client with credentials
    keyID,key = read_aws_creds()
    s3Client = boto3.client('s3',aws_access_key_id=keyID,aws_secret_access_key=key)

    # Set the file prefix string
    prefix = f'{product}/{year}/{day:03.0f}/{hour:02.0f}/OR_{product}-{scanMode}C{band:02.0f}'

    # Get the keys from the S3 bucket
    keys = get_s3_keys(bucketName,s3Client,prefix)

    # Selecting the first measurement taken within the hour
    key = [key for key in keys][0] 

    # Send a request to the bucket
    resp = requests.get(f'https://{bucketName}.s3.amazonaws.com/{key}')

    # Open the GOES 16 image
    fileName = key.split('/')[-1].split('.')[0]
    nc4 = netCDF4.Dataset(fileName,memory=resp.content)
    store = xr.backends.NetCDF4DataStore(nc4)
    ds = xr.open_dataset(store)

    return ds

def read_goes_ibtracs(filePath,subsetSeason=False,yearStart=0,yearEnd=3000):

    """Read IBTrACS data, after it has been filtered from the GOES full disc spatial range, to a pandas data frame, subset seasons if needed"""

    # Read the data from the CSV
    df = pd.read_csv(filePath)

    # Convert time strings to datetimes for better querying
    df['ISO_TIME'] = pd.to_datetime(df['ISO_TIME'])
    df['SEASON'] = pd.to_numeric(df['SEASON'])
    df['NUMBER'] = pd.to_numeric(df['NUMBER'])
    df['LAT'] = pd.to_numeric(df['LAT'])
    df['LON'] = pd.to_numeric(df['LON'])

    # Subset seasons
    if subsetSeason:
        df = df[(df['SEASON'] >= yearStart) & (df['SEASON'] <= yearEnd)]

    return df