from .base import BaseAPIClient
from typing import Dict, List
import requests
from pathlib import Path
import pandas as pd
from io import StringIO
from typing import Optional, Dict, List
import time
from indicator.models import Indicator
from institution.models import Institution
import json
IMF_ENDPOINT = "https://www.imf.org/external/datamapper/api/v1"


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
    def __init__(self, mode='e'):
        super().__init__(base_endpoint=IMF_ENDPOINT)
        self.logger.info("IMF API client initialized")
        self.mode = mode
        self.IMF_DIR = self.BASE_DIR / 'data' / 'imf'
        self.IMF_upload_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        self.file_path = self.IMF_DIR /  f"IMF_ECONOMIC_OUTLOOK_{self.IMF_upload_date}.json"
        self.file_path_for_loading = self.IMF_DIR / "imf_data_transformed.csv"
        self.column_mapping = {

        }
        self.dtypes = {}
        self.institution = "IMF"
        self.IMF_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_COLUMNS = ["inst_instid", "indic_indicid", "area_areaid", 
                           "date_published", "date_from", "date_until",
                           "value",  
                           "is_forecast"]

    def run_transform(self) -> pd.DataFrame:
        self.logger.info(f"Start transforming data from {self.file_path}")
        with open(self.file_path, 'r') as f:
            jsondata = json.loads(f.read())
        df = pd.DataFrame(columns=self.DB_COLUMNS)
        self.logger.info("Start unpacking data")
        df = self.unpack_symbol(jsondata)
        self.logger.info("Data unpacked")
        self.logger.info("Parsing dates")
        df["date_from"] = pd.to_datetime(df["date_from"])
        df["date_until"] = df["date_from"] + pd.DateOffset(years=1)
        df["date_published"] = pd.Timestamp(f"{pd.Timestamp.now().year}-01-01")
        self.logger.info("Classifying forecast data")
        df['is_forecast'] = 'N'
        df.loc[df['date_from'] >= df['date_published'], 'is_forecast'] = 'Y'
        df.to_csv(self.file_path_for_loading, index=False)
        self.logger.info("Data transformed and saved to local file")

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
        self.logger.info("Data extracted")
        self.logger.info("indicators: " + str(data.keys()))
        self.save_data(data)
        self.logger.info("Data saved to local file")

    def setup_endpoints(self) -> List[str]:
        institution_id = Institution.objects.get(abbreviation = self.institution)
        indicators = Indicator.objects.filter(inst_instid = institution_id).values('abbreviation').values()
        indicators_set = list({indicators[i]['abbreviation'] for i in range(len(indicators))})
        return [self.base_endpoint + f"/{indicator}" for indicator in indicators_set]
        
    def merge_responses(self, responses: List[requests.Response]) -> dict:
        merged_response = {}
        for response in responses:
            merged_response.update(response.json()['values'])
        return merged_response

    def save_data(self, data: str) -> None:
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def unpack_symbol(self, jsondata: Dict) -> pd.DataFrame:
        result = [
            (self.institution, indicator, area, '', year,'', value, '')
            for indicator, sub_dict1 in jsondata.items()
            for area, sub_dict2 in sub_dict1.items()
            for year, value in sub_dict2.items()
        ]
        df_result = pd.DataFrame(result, columns=self.DB_COLUMNS)
        return df_result
    