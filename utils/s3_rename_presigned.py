import boto3
import requests
from dotenv import load_dotenv
import os
# Load the.env file
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
def create_presigned_url_for_rename(bucket_name, current_key, new_key, expiration=3600):
    """
    Generate a presigned URL for renaming an S3 object

    :param bucket_name: string
    :param current_key: Current key (path) of the file in S3
    :param new_key: New key (path) for the file
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="eu-north-1",
        config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
    )
    try:
        response = s3_client.generate_presigned_url('copy_object',
                                                    Params={'Bucket': bucket_name,
                                                            'CopySource': f'{bucket_name}/{current_key}',
                                                            'Key': new_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return e

    return response

def rename_and_delete_old_s3_file(current_key, new_key):
    """
    Rename a file in S3 by generating a presigned URL for the new file name, performing the rename operation through it,
    and then deleting the old file.

    :param bucket_name: Name of the bucket where the file is located
    :param current_key: Current key (path) of the file in S3
    :param new_key: New key (path) for the file
    """
    bucket_name = 'tarantula-ai-marketplace-app-website-builder'
    presigned_url = create_presigned_url_for_rename(bucket_name, current_key, new_key)

    if presigned_url:
        headers = {'x-amz-copy-source': f"{bucket_name}/{current_key}"}
        response = requests.put(presigned_url, headers=headers)

        if response.status_code == 200:
            print("File successfully renamed.")
            # Delete the old file
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name="eu-north-1",
                config=boto3.session.Config(signature_version='s3v4', s3={'signature_version': 's3v4', 'use_accelerate_endpoint': False})
            )
            s3_client.delete_object(Bucket=bucket_name, Key=current_key)
            print("Old file deleted successfully.")
            return "New file copied succesfully. Old file deleted successfully."
        else:
            print(f"Failed to rename file. Status code: {response.status_code}")
            return f"Failed to rename file. Status code: {response.status_code}"
    else: 
        print("Failed to create presigned URL for copy")
        return "Failed to create presigned URL for copy"

# # Example usage
# current_key = '1/hello1234.txt'
# new_key = '2/hello1234.txt'

# rename_and_delete_old_s3_file(current_key, new_key)
