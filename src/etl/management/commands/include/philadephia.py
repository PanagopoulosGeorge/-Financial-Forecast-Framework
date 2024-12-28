import pandas as pd
from .base import BaseAPIClient
from indicator.models import Publishes
from institution.models import Institution
from geography.models import Area
import numpy as np
import time
url = 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/spf-q4-2023'

class PhiladelphiaClient(BaseAPIClient):
    def __init__(self, url, mode='t'):
        super().__init__(url)
        self.mode = mode
        self.url = url
        self.institution = 'FRBP'
        self.data = self.get_data()
        self.PHILADELPHIA_DIR = self.BASE_DIR / 'data' / 'philadelphia'
        self.forecasts = [self.data[0]] + [self.data[1]]
        self.year_published = self.url.split('-')[-1]
        self.quarter_published = self.url.split('-')[-2].upper()
        self.date_published = self.parse_date(f"{self.year_published}-{self.quarter_published}")
        self.file_path = self.PHILADELPHIA_DIR /  f"PHILADELPHIA_SPF_{self.year_published}-{self.quarter_published}.csv"
        self.file_path_for_loading = self.PHILADELPHIA_DIR /  f"FRBP_data_transformed_{self.year_published}-{self.quarter_published}.csv"
        self.logger.info(f"Philadelphia URL: {self.url}")
        self.logger.info(f"Philadelphia file path: {self.file_path}")
        self.PHILADELPHIA_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_COLUMNS = ['inst_instid','indic_indicid','area_areaid','date_published','date_from','date_until','value','is_forecast']
        self.area = 'USA'
        self.indicator_mapping = {
            'Real GDP (%)' : 'RGDP',
            'Unemployment Rate (%)' : 'UR',
            'Payrolls (000s/month)' : 'PL',
            'Headline CPI' : 'HCPI',
            'Core CPI' : 'CCPI',
            'Headline PCE' : 'HPCE',
            'Core PCE' : 'CPCE',
        }
    
    def get_data(self):
        tables = pd.read_html(self.url)
        return tables
    
    def run_extract(self):
        time.sleep(1)
        dfs = []
        for forecast in self.forecasts:
            if forecast.empty:
                self.logger.info("No data found")
                return
            self.logger.info("Start unpacking data")
            df = forecast.copy()
            self.logger.info("Filtering out 'previous' columns")       
            column_masking = [col for col in df.columns if col[1].lower() != 'previous']
            try:
                df = self.flatten_columns(df[column_masking])
                self.logger.info("Parsing date column")
                df = self.handle_date_column(df)
            except Exception as e:
                self.logger.error(f"An error occurred during data extraction: {e}")
                raise
            self.logger.info("Data extracted")
            dfs.append(df)
        df1, df2 = dfs
        final_df = df1.merge(df2, on=['date_from', 'FREQ'], how='outer')
        final_df.to_csv(self.file_path, index=False)
        self.logger.info(f"Data saved to {self.file_path}")

    def flatten_columns(self, df):
        df.columns = [col[0] for col in df.columns.values]
        return df
    
    def handle_date_column(self, df):
        date_column = df.columns[0]
        df.rename(columns={date_column: 'date_from'}, inplace=True)
        self.logger.info("Data columns: " + str(df.columns))
        self.logger.info("Data records: " + str(df.shape[0]))
        date_related_mask = df['date_from'].str.contains(r'\b20[0-9]{2}', na=False) & (df['date_from'].str.len() <= 7)
        
        df = df[date_related_mask].copy()
        self.logger.info("Data records after date filtering: " + str(df.shape[0]))
        df.reset_index(drop=True, inplace=True)
        df['date_from'] = df['date_from'].str.replace(':', '-')
        df['FREQ'] = df['date_from'].apply(lambda x: 'A' if len(x) == 4 else 'Q')
        try:
            df['date_from'] = df['date_from'].apply(self.parse_date)
        except Exception as e:
            self.logger.error(f"Error parsing date column: {e}")
            raise
        df.dropna(axis=1, how='all', inplace=True)
        return df

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

    def run_transform(self):
        time.sleep(1)
        self.logger.info("Start transforming data")
        try:
            df = pd.read_csv(self.file_path)
        except Exception as e:
            self.logger.error(f"Not Exists: {e}")
            raise
        self.logger.info("Data loaded")
        unpivoted_df = df.melt(id_vars=['date_from', 'FREQ'], value_vars=self.indicator_mapping,
                    var_name='indic_indicid', value_name='value')
        transformed_df = pd.DataFrame(columns=self.DB_COLUMNS)
        transformed_df['indic_indicid'] = unpivoted_df['indic_indicid'].map(self.indicator_mapping)
        transformed_df['inst_instid'] = self.institution
        transformed_df['area_areaid'] = self.area
        transformed_df['date_published'] = self.date_published
        transformed_df['date_from'] = pd.to_datetime(unpivoted_df['date_from'])
        transformed_df['date_until'] = unpivoted_df.apply(lambda x: 
                                                          pd.to_datetime(x['date_from']) + pd.DateOffset(years=1) if x['FREQ'] == 'A' else pd.to_datetime(x['date_from']) + pd.DateOffset(months=3), axis=1)
        transformed_df['value'] = unpivoted_df['value'].replace('N.A.', np.nan)
        transformed_df.dropna(subset=['value'], inplace=True)
        transformed_df['is_forecast'] = 'Y'
        transformed_df.to_csv(self.file_path_for_loading, index=False)
        self.logger.info(f"Data transformed and saved to {self.file_path_for_loading}")
