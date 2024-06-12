import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
# Load the.env file
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
def create_folder(folder_path):
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="eu-north-1",
        config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
    )
    
    try:
        # List objects under the specified folder path
        response = s3_client.list_objects_v2(Bucket='tarantula-ai-marketplace-app-website-builder', Prefix=folder_path)
        
        # Check if the folder exists (i.e., if there are no objects listed)
        if 'Contents' not in response or len(response.get('Contents', [])) == 0:
            # Folder does not exist, attempt to create it
            response = s3_client.put_object(Bucket='tarantula-ai-marketplace-app-website-builder', Key=folder_path)
            
            # Check if the operation was successful
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("Folder created successfully.")
                return f"Folder {folder_path} created successfully.",True
            else:
                print("Failed to create folder.")
                return "Failed to create folder.",False
        else:
            # Folder already exists
            print("Folder already exists.")
            return "Folder already exists.",True
    except NoCredentialsError:
        print("No AWS credentials found")
        return "No AWS credentials found",False

# # Example usage
# folder_path = 'sk-1ijqjadaldl100lkdlal0/'
# create_folder(folder_path)
