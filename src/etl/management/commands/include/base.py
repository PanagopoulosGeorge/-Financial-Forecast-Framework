import requests
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List
import concurrent.futures
import pandas as pd
import numpy as np
from institution.models import Institution
from indicator.models import Indicator, Publishes
from geography.models import Area
import warnings
warnings.filterwarnings("ignore")
BASE_DIR = Path(__file__).resolve().parent.parent


class BaseAPIClient(ABC):

    """
    This abstract class provides basic functionality for making HTTP requests to APIs
    and downloading the response data to local files.

    Args:
        endpoint (str): The base API endpoint URL
        timeout (int, optional): Request timeout in seconds. Defaults to DEFAULT_TIMEOUT (60)
        params (Dict, optional): Query parameters to include in requests. Defaults to None
        headers (Dict, optional): HTTP headers to include in requests.

    Basic Functionality:
        - _setup_logger: Setup logger for the API client
        - Main entry function
            download_local: Downloads API response data to local files

    To employ the concurrent request functionality, 
    construct an inhenerited class that implements 
    the following abstract methods:
        - setup_endpoints: define how the API endpoints are constructed based on the base endpoint
        - merge_responses methods: define how the responses are merged into a single data structure

    """
    DEFAULT_TIMEOUT = 60

    def __init__(
            self,
            base_endpoint: str,
            timeout: int = DEFAULT_TIMEOUT,
            params: Optional[Dict] = {},
            headers: Optional[Dict] = {}):
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = self.BASE_DIR / "data"
        self.base_endpoint = base_endpoint
        self.params = params
        self.headers = headers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.logger = self._setup_logger()
        self.logger.info(
            f"API client initialized with endpoint: {self.base_endpoint}")

    def _setup_logger(self) -> logging.Logger:
        """
        Set up a logger for the API client.

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def download_local(
        self,
        out_path: Optional[Path] = None,
        filename: Optional[str] = None,
        parent_mkdirs: bool = True
    ) -> bool:
        """
        Downloads data from the API and saves it locally.

        """
        if out_path is None:
            out_path = self.DATA_DIR

        if not isinstance(out_path, Path):
            raise ValueError("out_path must be a Path object")

        if parent_mkdirs:
            out_path.mkdir(parents=True, exist_ok=True)
        try:
            response = self._get_data(endpoint=self.base_endpoint)
            file_path = out_path / filename
            file_path.write_bytes(response.content)
            self.logger.info(f"Data downloaded to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to download data: {e}")
            return False

    def _get_data(self, endpoint) -> requests.Response:
        """
        Fetches data from the API.
        """
        response = self.session.get(endpoint,
                                    allow_redirects=True,
                                    params=self.params,
                                    headers=self.headers,
                                    timeout=self.timeout)
        response.raise_for_status()
        return response

    def setup_endpoints(self) -> List[str]:
        pass

    def _get_data_concurrent(self):
        """
        Fetches data from the API using concurrent requests.

        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._get_data, endpoint)
                       for endpoint in self.setup_endpoints()]
            results = [future.result()
                       for future in concurrent.futures.as_completed(futures)]
        return results

    def merge_responses(self, responses: List[requests.Response]):
        pass
    
    def run_load(self):
        self.logger.info(f"Start loading data from {self.file_path_for_loading}")
        df = pd.read_csv(self.file_path_for_loading)
        self.logger.info(f"Data loaded from {self.file_path_for_loading}")
        ###############################################################################################################
        ##################################   Query institution       ##################################################
        ###############################################################################################################
        self.logger.info(f"Retrieving institution instance")
        institution = df.loc[0, 'inst_instid']
        try:
            institution_instance = Institution.objects.get(abbreviation=institution)
        except Institution.DoesNotExist:
            self.logger.error(f"Could not find institution with abbreviation {institution}")
            return
        self.logger.info(f"Retrieved institution instance {institution}")
        ###############################################################################################################
        ###############################    Indicators - areas serialization             ###############################
        ###############################################################################################################
        self.logger.info(f"Serializing indicators and areas from database")
        indicator_mapper = {indicator.abbreviation : indicator for indicator in Indicator.objects.filter(inst_instid=institution_instance)}
        area_mapper = {area.code : area for area in Area.objects.all()}
        self.logger.info(f"Serialized {len(indicator_mapper)} indicators and {len(area_mapper)} areas")
        ###############################################################################################################
        ###############################    Split Data frame (projections, historized)   ###############################
        ###############################################################################################################
        self.logger.info(f"Splitting data into projections and historical data")
        projections = df[df['is_forecast'] == 'Y']
        historical = df[df['is_forecast'] == 'N']
        self.logger.info(f"Historical data: {len(historical)} records")
        self.logger.info(f"Projections data: {len(projections)} records")
        ###############################################################################################################
        ###############################    Prepare projections and bulk insert   ######################################
        ###############################################################################################################
        try:
            self.logger.info(f"Serializing projections data and inserting to database")
            projections_instances = self.serialize_records(projections, institution_instance, indicator_mapper, area_mapper)
            Publishes.objects.bulk_create(projections_instances, batch_size=1000) 
            self.logger.info(f"Inserted {len(projections_instances)} records")
        except Exception as e:
            self.logger.error(f"An error occurred during projections data insertion: {e}")
        ###############################################################################################################
        ###############################    Prepare historized and bulk insert   ######################################
        ###############################################################################################################
        try:
            self.logger.info(f"Serializing historized data and inserting to database")
            historized_instances = self.serialize_records(historical, institution_instance, indicator_mapper, area_mapper, 
                                                        mode='H')
            Publishes.objects.bulk_create(historized_instances, batch_size=1000) 
            self.logger.info(f"Inserted {len(historized_instances)} records")
            self.logger.info(f"Data loaded successfully")
        except Exception as e:
            self.logger.error(f"An error occurred during historized data insertion: {e}")
       
    def serialize_records(self, df: pd.DataFrame, 
                          
                          institution: Institution,
                          indicator_mapper: Dict,
                          area_mapper: Dict,
                          mode='P') -> List[Publishes]:
        serialized_instances = []
        if mode == 'H':
            existing_records = Publishes.objects.filter(inst_instid=institution, is_forecast='N').values(
                'indic_indicid', 'area_areaid', 'date_from', 'date_until', 'value')
            existing_records_mapper = {
                                    (record['indic_indicid'], record['area_areaid'], record['date_from'], record['date_until']) : float(record['value'])
            for record in existing_records
            }
        for _, row in df.iterrows():
            indicator = indicator_mapper.get(row['indic_indicid'], None)
            area = area_mapper.get(row['area_areaid'], None)

            if not indicator or not area:
                continue
                
            if mode == 'H':
                key_record = (indicator.indicid, area.areaid, pd.to_datetime(row['date_from']), pd.to_datetime(row['date_until']))
                if key_record in existing_records_mapper:
                    if existing_records_mapper[key_record] == float(row['value']):
                        # self.logger.info("Skipping record")
                        continue  
            
            instance = Publishes(
                inst_instid = institution,
                indic_indicid = indicator,
                area_areaid = area,
                date_published=row['date_published'],
                date_from=row['date_from'],
                date_until=row['date_until'],
                value=row['value'],
                is_forecast=row['is_forecast'],
                created_at=pd.Timestamp.now()
            )
            serialized_instances.append(instance)
        self.logger.info(f"Serialized {len(serialized_instances)} records")
        return serialized_instances
    