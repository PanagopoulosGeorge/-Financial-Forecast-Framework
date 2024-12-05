from .base import BaseAPIClient
from typing import Dict, List
import requests
from pathlib import Path
import pandas as pd
from io import StringIO
from .utils import get_last_upload_date_OECD
from typing import Optional, Dict, List
# from indicator.models import Publishes, Indicator
OECD_HEADERS = {
    'Accept': 'application/vnd.sdmx.data+csv; charset=utf-8; version=2'
}
OECD_ENDPOINT = "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO@DF_EO"
OECD_PARAMS = {}


class OECDClient(BaseAPIClient):
    def __init__(self, params: Optional[Dict] = {}, headers: Optional[Dict] = {}):
        super().__init__(base_endpoint=OECD_ENDPOINT, params=params, headers=OECD_HEADERS)
        self.base_endpoint = self.setup_endpoints()

    def setup_endpoints(self):
        """
        Construct the API endpoints based on the base endpoint.
        """
        return self.base_endpoint + "/GRC..A"

    def merge_responses(self) -> pd.DataFrame:
        """
        Merge the responses into a single data structure (Pandas Dataframe).
        """
        pass

    def transform_data(self, data: str) -> pd.DataFrame:
        """
        Transform the original data into the database table's schema.
        """


if __name__ == "__main__":
    oecd = OECDClient()
    oecd.logger.info("OECD API client initialized")
    oecd.logger.info("Endpoint: " + oecd.base_endpoint)
    oecd.download_local(filename="OECD_Economic_Outlook_GREECE_Annual.csv")
    oecd.logger.info("Data downloaded successfully")
