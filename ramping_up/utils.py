
import datetime
import os

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