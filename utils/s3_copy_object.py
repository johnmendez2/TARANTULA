import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
# Load the.env file
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
def generate_presigned_copy(old_key, new_key):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="eu-north-1",
        config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
    )
    try:
        # Generate pre-signed URL for copying (renaming)
        response = s3_client.generate_presigned_url('copy_object',
                                                     Params={
                                                         'Bucket': 'tarantula-ai-marketplace-app-website-builder',
                                                         'CopySource': {'Bucket': 'tarantula-ai-marketplace-app-website-builder', 'Key': old_key},
                                                         'Key': new_key
                                                     })
        return response
    except NoCredentialsError:
        print("No AWS credentials found")
        return None

