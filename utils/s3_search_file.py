import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
# Load the.env file
AWS_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
def find_files_by_search_string(user_id, project_name, search_string):
    # Initialize an empty list to hold the matching file paths
    matching_files = []
    
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_ACCESS_KEY,
        region_name="eu-north-1",
        config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
    )

    # Construct the user-specific path within the S3 bucket
    user_specific_path = f"{user_id}/{project_name}/"
    
    # List objects in the bucket that match the user-specific path
    response = s3_client.list_objects_v2(Bucket='tarantula-ai-marketplace-app-website-builder', Prefix=user_specific_path)
    
    # Filter objects based on the search string
    if 'Contents' in response:
        for obj in response['Contents']:
            if search_string.lower() in obj['Key'].lower():
                matching_files.append(obj['Key'])
    
    return matching_files

# Example usage
# user_id = "2"
# project_name = "example_project_name"
# search_string = "hello"
# matching_files = find_files_by_search_string(user_id, project_name, search_string)
# print("Matching files:", matching_files)
