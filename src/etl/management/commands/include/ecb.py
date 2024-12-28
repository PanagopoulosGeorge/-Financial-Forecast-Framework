from html.parser import HTMLParser
import requests
import pandas as pd
from .base import BaseAPIClient
import numpy as np
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
class ECBParser(HTMLParser):
    def __init__(self, *, convert_charrefs = True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.recording = 0
        self.data = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value in ('#inflation', '#core', '#gdp', '#unemployment'):
                    #print("Encountered the beginning of a %s tag" % tag)
                    #print(name, value)
                    self.recording = 1
        
    def handle_endtag(self, tag):
        if tag == 'a':
            if self.recording == 1:
                self.recording -= 1
                #print("Encountered the end of a %s tag" % tag)
    
    def handle_data(self, data):
        if self.recording:
            #print("Encountered some data  :", data)
            self.data.append(data)
            #print(self.data)

class ECBClient(BaseAPIClient):
    def __init__(self, url, mode='t'):
        super().__init__(url)
        self.mode = mode
        self.url = url
        self.date_index_end = url.find('.en')
        self.date_index_start = self.date_index_end - 6
        self.year_published = url[self.date_index_start:self.date_index_end][:4]
        self.quarter_published = url[self.date_index_end-1]
        self.date_published = self.parse_date(self.year_published + '-Q' + self.quarter_published)
        self.institution = 'ECB'
        self.area = 'EA17'  ## Euro Area
        self.labels = self.get_columns()
        self.raw_tables = self.get_data()
        self.filtered_measures = ['Mean point estimate', 'Standard deviation']
        self.measure_mapping = {
            'Mean point estimate' : '_MPE',
            'Standard deviation' : '_STD',
        }
        self.indicator_mapping = {
            'Inflation forecasts' : 'HICP',

            'Core inflation forecasts' : 'CHICP',

            'Real GDP growth forecasts' : 'RGDP',

            'Unemployment rate forecasts' : 'UR',
        } 
        self.DB_COLUMNS = ['inst_instid','indic_indicid','area_areaid','date_published','date_from','date_until','value','is_forecast']
        if not self.raw_data_reconciled():
            raise ValueError("Data not reconciled")
        self.ECB_DIR = self.BASE_DIR / 'data' / 'ecb'
        self.file_path = self.ECB_DIR /  f"ECB_{self.year_published}-Q{self.quarter_published}.csv"
        self.file_path_for_loading = self.ECB_DIR /  f"ECB_data_transformed.csv"
        self.ECB_DIR.mkdir(parents=True, exist_ok=True)

    def filter_table(self, table):
        mask = table['measure'].isin(self.filtered_measures)
        return table[mask]
    
    def run_extract(self):
        self.logger.info("Running extract for ECB")
        renaming = {'Unnamed: 0': 'measure'}
        dfs = []
        for table, label in zip(self.raw_tables, self.labels):
            table = table.rename(columns=renaming)
            filtered_table = self.filter_table(table)
            try:
                filtered_table['indicator'] = self.indicator_mapping[label] + filtered_table['measure'].map(self.measure_mapping)
            except KeyError:
                self.logger.info(f"Indicator not found for {label}")
                raise KeyError
            dfs.append(filtered_table)
        self.data = pd.concat(dfs)
        self.data.to_csv(self.file_path, index=False)
    
    def run_transform(self):
        self.logger.info("Start transforming data")
        try:
            df = pd.read_csv(self.file_path)
        except Exception as e:
            self.logger.error(f"Not Exists: {e}")
            raise
        self.logger.info("Data loaded")
        unpivoted_df = df.melt(id_vars=['measure', 'indicator'], var_name = 'date_from', value_name = 'value')
        unpivoted_df = self.handle_date_column(unpivoted_df)
        transformed_df = pd.DataFrame(columns=self.DB_COLUMNS)
        transformed_df['indic_indicid'] = unpivoted_df['indicator']
        transformed_df['inst_instid'] = self.institution
        transformed_df['area_areaid'] = self.area
        transformed_df['date_published'] = self.date_published
        transformed_df['date_from'] = pd.to_datetime(unpivoted_df['date_from'])

        transformed_df['date_until'] = unpivoted_df.apply(lambda x: 
                                                          pd.to_datetime(x['date_from']) + pd.DateOffset(years=1), axis=1)
        transformed_df['value'] = unpivoted_df['value'].replace('N.A.', np.nan)
        transformed_df.dropna(subset=['value'], inplace=True)
        transformed_df['is_forecast'] = 'Y'
        transformed_df.to_csv(self.file_path_for_loading, index=False)
        self.logger.info(f"Data transformed and saved to {self.file_path_for_loading}")

    def raw_data_reconciled(self):
        if len(self.labels) == 0:
            raise ValueError("No columns found")
        if len(self.raw_tables) == 0:
            raise ValueError("No tables found")
        if len(self.raw_tables) != len(self.labels):
            raise ValueError("Number of tables and columns do not match")
        return True

    def handle_date_column(self, df):
        self.logger.info("Data columns: " + str(df.columns))
        self.logger.info("Data records: " + str(df.shape[0]))
        date_related_mask = df['date_from'].str.contains(r'\b20[0-9]{2}', na=False)
        df = df[date_related_mask].copy()
        self.logger.info("Data records after date filtering: " + str(df.shape[0]))
        df.reset_index(drop=True, inplace=True)
        df['date_from'] = df['date_from'].str.replace(' ', '-')
        # df['FREQ'] = df['date_from'].apply(lambda x: 'A' if len(x) == 4 else 'Q')
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
            try:
                from dateutil import parser
                return pd.Timestamp(parser.parse(date).replace(day=1))
            except ValueError:
                raise ValueError(f"Date {date} not in expected format")
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date}: {e}")
            raise

    def get_columns(self):
        try:
            col_parser = ECBParser()
            response = requests.get(self.url)
            response.raise_for_status()
        except Exception as err:
            print(err)
            return None
        col_parser.feed(response.text)
        return col_parser.data
    
    def get_data(self):
        tables = pd.read_html(self.url)
        return tables
