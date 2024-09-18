# Copyright 2024 Vikit.ai. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from google.cloud import storage
from google.auth.exceptions import GoogleAuthError
from google.api_core.exceptions import NotFound, Forbidden
from loguru import logger
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

class GoogleCloudStorageGateway:
    def __init__(self, credentials_path, bucket_name, token_path='token.pickle'):
        """
        Initializes the GoogleCloudStorageGateway class with the GCS bucket name and OAuth 2.0 authentication.

        :param bucket_name: The name of the GCS bucket where files will be uploaded.
        :param credentials_path: Path to the OAuth 2.0 client secrets JSON file.
        :param token_path: Path to the token.pickle file for storing the user's OAuth tokens.
        """
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.token_path = token_path

        try:
            self.credentials = self.authenticate_with_oauth()
            self.storage_client = storage.Client(credentials=self.credentials)
            logger.info("Authenticated successfully with OAuth and initialized the Storage client.")
        except (GoogleAuthError, FileNotFoundError) as e:
            logger.error(f"Error during authentication: {e}")
            raise Exception(f"Authentication failed. Please check your OAuth credentials. Error: {e}")

    def authenticate_with_oauth(self):
        """
        Handles OAuth 2.0 authentication. Checks for existing tokens, and if they don't exist or are invalid, it refreshes them.
        :return: OAuth 2.0 credentials object
        """
        credentials = None

        # Load existing tokens if they exist
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    credentials = pickle.load(token)
                logger.info("Loaded existing OAuth token from token.pickle.")
            except Exception as e:
                logger.error(f"Error loading token from {self.token_path}: {e}")
                raise

        # If there are no valid credentials available, refresh them or log in
        if not credentials or not credentials.valid:
            try:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    logger.info("Refreshed expired OAuth token.")
                else:
                    #flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, scopes=None)
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
                    credentials = flow.run_local_server(port=0)
                    logger.info("Authenticated with OAuth for the first time.")
                
                # Save the credentials for future use
                with open(self.token_path, 'wb') as token:
                    pickle.dump(credentials, token)
                    logger.info(f"Saved new OAuth token to {self.token_path}.")
            except FileNotFoundError as e:
                logger.error(f"OAuth credentials file not found: {self.credentials_path}. Error: {e}")
                raise
            except GoogleAuthError as e:
                logger.error(f"Authentication with OAuth failed. Error: {e}")
                raise

        return credentials

    def check_bucket_access(self):
        """
        Checks if a GCS bucket exists and if the application principal has access.
        """
        client = storage.Client()
        
        try:
            bucket = client.get_bucket(self.bucket_name)
            # If the above doesn't raise an exception, the bucket exists and the app can access it
            print(f"Bucket '{self.bucket_name}' exists and can be accessed.")
            return True
        except NotFound:
            print(f"Bucket '{self.bucket_name}' does not exist.")
            return False
        except Forbidden:
            print(f"Access to bucket '{self.bucket_name}' is denied.")
            return False

    def upload_image(self, source_file_path, destination_blob_name):
        """
        Uploads an image to Google Cloud Storage using OAuth 2.0 authentication and makes it publicly accessible.

        :param source_file_path: Path to the local file to be uploaded.
        :param destination_blob_name: The name of the blob (file) once uploaded in the GCS bucket.
        :return: The public URL of the uploaded image.
        """
        try:
            # Get the bucket
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # Check if the bucket exists
            if not bucket.exists():
                logger.error(f"The bucket {self.bucket_name} does not exist.")
                raise NotFound(f"Bucket {self.bucket_name} not found.")
            
            logger.info(f"Uploading file {source_file_path} to bucket {self.bucket_name} as {destination_blob_name}.")
            
            # Create a new blob (file) in the bucket
            blob = bucket.blob(destination_blob_name)
            
            # Upload the file to GCS
            blob.upload_from_filename(source_file_path)
            logger.info(f"Successfully uploaded {source_file_path} to {self.bucket_name}/{destination_blob_name}.")
            
            # Make the file publicly accessible
            blob.make_public()
            logger.info(f"Made {destination_blob_name} publicly accessible.")
            
            # Return the public URL
            public_url = blob.public_url
            return public_url
        except FileNotFoundError as e:
            logger.error(f"File {source_file_path} not found. Error: {e}")
            raise
        except NotFound as e:
            logger.error(f"Bucket {self.bucket_name} or file not found. Error: {e}")
            raise
        except Forbidden as e:
            logger.error(f"Access denied to bucket {self.bucket_name}. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to upload image. Error: {e}")
            raise

# Example usage:
# storage_client = CloudStorage('your-bucket-name', 'path/to/oauth-credentials.json')

# try:
#     public_url = storage_client.upload_image('path/to/local/image.jpg', 'uploads/image.jpg')
#     print(f"Publicly accessible URL: {public_url}")
# except Exception as e:
#     logger.error(f"Failed to upload image: {e}")
