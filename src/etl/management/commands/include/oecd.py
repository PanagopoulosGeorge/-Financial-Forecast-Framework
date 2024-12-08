from .base import BaseAPIClient
from typing import Dict, List
import requests
from pathlib import Path
import pandas as pd
from io import StringIO
from .utils import get_last_upload_date_OECD
from typing import Optional, Dict, List
import time
from indicator.models import Publishes
from institution.models import Institution
OECD_HEADERS = {
    'Accept': 'application/vnd.sdmx.data+csv; charset=utf-8; version=2'
}
OECD_ENDPOINT_LAST = "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO@DF_EO"
OECD_PARAMS = {}


class OECDClient(BaseAPIClient):
    def __init__(self, mode='t'):
        super().__init__(base_endpoint=OECD_ENDPOINT_LAST,
                         headers=OECD_HEADERS, params=OECD_PARAMS)
        self.logger.info("OECD API client initialized")
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
        self.logger.info(f"Start transforming data from {self.file_path}")
        try:
            # File existance check
            if not self.file_path.exists():
                raise FileNotFoundError(
                    f"Data file not found. Run in 'e' mode first")
            # Load data
            raw_data = pd.read_csv(self.file_path, dtype=self.dtypes,)
            self.logger.info("Data shape: " + str(raw_data.shape))

            # Validate data
            if raw_data.empty:
                raise ValueError("Data is empty")

            # Rename columns
            raw_data.rename(columns=self.column_mapping, inplace=True)

            # Drop null values
            raw_data.dropna(subset=['area_areaid', 'indic_indicid', 'value', 'date_from', 'FREQ'],
                            inplace=True)
            self.logger.info("Data shape after dropping nulls: " +
                             str(raw_data.shape))

            # Parse date - quarterly and annual - and create date_until
            self.logger.info("Parsing date columns")
            raw_data['date_from'] = raw_data['date_from'].apply(
                self.parse_date)
            raw_data['date_until'] = raw_data['date_from'] + pd.DateOffset(
                years=1)
            mask_quarterly = raw_data['FREQ'] == 'Q'
            raw_data.loc[mask_quarterly, 'date_until'] = raw_data.loc[mask_quarterly, 'date_from'].apply(
                lambda x: x + pd.DateOffset(months=3))
            raw_data['date_published'] = pd.to_datetime(self.OECD_upload_date)

            # Classify forecast data
            self.logger.info("Classifying forecast data")
            raw_data['is_forecast'] = 'N'
            mask_forecast = raw_data['date_from'] >= pd.to_datetime(
                self.OECD_upload_date)
            raw_data.loc[mask_forecast, 'is_forecast'] = 'Y'

            # Add institution id
            raw_data['inst_instid'] = self.institution
            transformed_df = raw_data[['inst_instid', 'indic_indicid', 'area_areaid',
                                       'date_published',  'date_from',  'date_until', 'value', 'is_forecast']].copy()
            transformed_df.to_csv(self.file_path_for_loading, index=False)
        except Exception as e:
            self.logger.error(
                f"An error occurred during data transformation: {e}")
            raise
        self.logger.info(f"Data transformed and saved to {self.file_path_for_loading}")

    def parse_date(self, date: str) -> pd.Timestamp:
        try:
            if len(date) == 4:
                return pd.Timestamp(date + "-01-01")
            if len(date) == 7 and "-Q" in date:
                year, quarter = date.split("-Q")
                month = int(quarter) * 3 - 2
                return pd.Timestamp(f"{year}-{month:02d}-01")
            return pd.Timestamp(date)
        except Exception as e:
            self.logger.error(f"Error parsing date {date}: {e}")
            raise

    def run(self):
        if self.mode == 'etl':
            if self.database_up_to_date():
                self.logger.info(
                    "Database is up-to-date. Exiting ETL process")
                return
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
        time.sleep(1)

    def setup_endpoints(self) -> List[str]:
        return [self.base_endpoint + "/..A"] + [self.base_endpoint + "/..Q"]

    def merge_responses(self, responses: List[requests.Response]) -> str:
        merged_list = responses[0].text.split(
            '\r\n')[:-1] + responses[1].text.split('\r\n')[1:-1]
        return '\n'.join(merged_list)

    def save_data(self, data: str) -> None:
        with open(self.file_path, "w") as f:
            f.write(data)
    
    def database_up_to_date(self) -> bool:
        return self.get_last_update() >= self.OECD_upload_date
    
    def get_last_update(self) -> Optional[str]:
        try:
            institution_id = Institution.objects.get(abbreviation=self.institution)
        except Institution.DoesNotExist:
            self.logger.error(f"Institution {self.institution} does not exist")
            return "0000"
        try:
            last_update = Publishes.objects.filter(inst_instid=institution_id).latest('date_published').date_published
        except Publishes.DoesNotExist:
            self.logger.info(f"No data found for {self.institution} in database")
            return "0000"
        last_update_date = last_update.__str__().split(' ')[0]
        return last_update_date
    
