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

# This test suite is used to test the Google Cloud Storage integration needed to upload image files
# to a GCS bucket, later used by Haiper to generate image-based videos


import warnings

import pytest
from loguru import logger

from vikit.common.config import get_google_cloud_auth_credentials, get_google_cloud_storage_bucket_name
from vikit.gateways.gcs_cloud_storage_gateway import GoogleCloudStorageGateway

class TestGoogleCloudStorage:

    def setUp(self) -> None:
        warnings.simplefilter("ignore", category=ResourceWarning)
        warnings.simplefilter("ignore", category=UserWarning)
        logger.add("log_test_google_cloud_storage.txt", rotation="10 MB")

    @pytest.mark.local_integration
    def test_get_config(self):
        
        print("Google Cloud Storage OAuth Credentials file location", get_google_cloud_auth_credentials())
        assert len(get_google_cloud_auth_credentials()) > 0  # we should have a non-null file location
        print("Google Cloud Storage bucket name", get_google_cloud_storage_bucket_name())
        assert len(get_google_cloud_storage_bucket_name()) > 0  # we should have a non-null file location
        get_google_cloud_storage_bucket_name

    def test_auth(self):
        auth_creds = get_google_cloud_auth_credentials()
        bucket_name = get_google_cloud_storage_bucket_name()
        gcs = GoogleCloudStorageGateway(auth_creds, bucket_name)
        gcs.authenticate_with_oauth()

    def test_bucket_exists(self):
        auth_creds = get_google_cloud_auth_credentials()
        bucket_name = get_google_cloud_storage_bucket_name()
        gcs = GoogleCloudStorageGateway(auth_creds, bucket_name)
        gcs.authenticate_with_oauth()

        assert gcs.check_bucket_access() == True

    