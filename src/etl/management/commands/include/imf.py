from .base import BaseAPIClient
from typing import Dict, List
import requests
from pathlib import Path
import pandas as pd
from io import StringIO
from .utils import get_last_upload_date_OECD
from typing import Optional, Dict, List
import time
OECD_HEADERS = {
    'Accept': 'application/vnd.sdmx.data+csv; charset=utf-8; version=2'
}
OECD_ENDPOINT = "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO@DF_EO"
OECD_PARAMS = {}

"""
1. Change the endpoints and headers to IMF
2. change the __init__ method to accept IMF parameters
3. Change the column_mapping to IMF columns
4. Change the dtypes to IMF dtypes
5. Change the institution to IMF
6. Change the setup_endpoints method to return IMF endpoints
7. Change the merge_responses method to merge IMF responses
7. rewrite the run_transform method to transform IMF data
"""
class IMFClient(BaseAPIClient):
    def __init__(self, mode='t'):
        super().__init__(base_endpoint=OECD_ENDPOINT,
                         headers=OECD_HEADERS, params=OECD_PARAMS)
        self.logger.info("IMF API client initialized")
        self.mode = mode
        self.OECD_upload_date = get_last_upload_date_OECD()
        self.OECD_DIR = self.BASE_DIR / 'data' / 'oecd'
        self.file_path = self.OECD_DIR /  f"OECD_ECONOMIC_OUTLOOK_{self.OECD_upload_date}.csv"
        self.file_path_for_loading = self.OECD_DIR / "oecd_data_transformed.csv"
        self.column_mapping = {
            "REF_AREA": "area_areaid",
            "MEASURE": "indic_indicid",
            "OBS_VALUE": "value",
            "TIME_PERIOD": "date_from",
        }
        self.dtypes = {"REF_AREA": str, "MEASURE": str,
                       "OBS_VALUE": float, "TIME_PERIOD": str}
        self.institution = "OECD"
        self.OECD_DIR.mkdir(parents=True, exist_ok=True)

    def run_transform(self) -> pd.DataFrame:
        pass

    def run(self):
        if self.mode == 'etl':
            self.run_extract()
            self.run_transform()
            self.run_load()
        elif self.mode == 'e':
            self.run_extract()
            return 
        elif self.mode == 't':
            self.run_transform()
        elif self.mode == 'l':
            self.run_load()
        else:
            raise ValueError("Invalid mode. Choose from 'etl' or 'extract'")

    def run_extract(self):
        responses = self._get_data_concurrent()
        data = self.merge_responses(responses)
        self.save_data(data)
        self.logger.info("Data saved to local file")

    def setup_endpoints(self) -> List[str]:
        pass

    def merge_responses(self, responses: List[requests.Response]) -> str:
        pass

    def save_data(self, data: str) -> None:
        pass
