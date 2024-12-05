import requests
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List
import concurrent.futures

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
