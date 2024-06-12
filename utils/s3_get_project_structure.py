import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
# Load the.env file
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
def list_directory_paths(user_id, project_name):
    # Initialize an empty list to hold the directory paths
    directory_paths = []
    
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="eu-north-1",
        config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
    )

    # Construct the user-specific path within the S3 bucket
    user_specific_path = f"{user_id}/{project_name}/"
    
    # Initialize variables for pagination
    continuation_token = None
    done = False
    
    while not done:
        if continuation_token:
            response = s3_client.list_objects_v2(Bucket='tarantula-ai-marketplace-app-website-builder', Prefix=user_specific_path, Delimiter='/',
                                                 ContinuationToken=continuation_token)
        else:
            response = s3_client.list_objects_v2(Bucket='tarantula-ai-marketplace-app-website-builder', Prefix=user_specific_path, Delimiter='/')
        
        # Process directories and files
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                directory_paths.append(prefix['Prefix'])  # Add directory path to the list
                # Recursively list objects within this directory
                list_directory_contents(s3_client, 'tarantula-ai-marketplace-app-website-builder', prefix['Prefix'], directory_paths)
                
        if 'Contents' in response:
            for obj in response['Contents']:
                directory_paths.append(obj['Key'])  # Add file path to the list
        
        # Check for more pages
        if 'NextContinuationToken' in response:
            continuation_token = response['NextContinuationToken']
        else:
            done = True
    
    return directory_paths

def list_directory_contents(s3_client, bucket_name, directory_path, directory_paths):
    """Recursively list objects within a directory."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory_path, Delimiter='/')
    if 'Contents' in response:
        for obj in response['Contents']:
            directory_paths.append(obj['Key'])  # Append file path to the list
    if 'CommonPrefixes' in response:
        for prefix in response['CommonPrefixes']:
            list_directory_contents(s3_client, bucket_name, prefix['Prefix'], directory_paths)  # Recurse into subdirectories

# Example usage
# user_id = "2"
# project_name = "example_project_name"
# directory_paths = list_directory_paths(user_id, project_name)
# print(directory_paths)
