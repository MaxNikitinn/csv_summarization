import pandas as pd
import numpy as np
import argparse
import datetime as dt
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from scipy import stats
import json


class TableHandler():
    def __init__(self, pandas_file, output_type, out_filename, datetime_cols, *args):
            
        # handling possible filename issues, preferencing reliability
        if output_type == 'markdown' and not out_filename.endswith('.txt'):
            out_filename += '.txt'
        if output_type == 'html' and not out_filename.endswith('.html'):
            out_filename += '.html'
        if output_type == 'xlsx' and not out_filename.endswith('.xlsx'):
            out_filename += '.xlsx'
        
        self.input_file = pandas_file
        self.output_type = output_type
        self.out_filename = out_filename
        self.datetime_cols = datetime_cols.split(',') if not datetime_cols is None else None
        self.args = args

    def parseDataset(self):
        '''
        Read csv file from a disc and calculate various metrics
        '''
        self.df_info = dict() # here the overall dataset info is stored
        self.info = dict() # here all the column metrics are stored
        self.df = pd.read_csv(self.input_file, parse_dates=self.datetime_cols)
        self.df_info.update({'rows' : self.df.shape[0]})
        self.df_info.update({'columns' : self.df.shape[1]})

        for column in self.df.columns:
            self.info.update({column:dict()})
            # self.info[column].update({'type':self.df[column].dtype})
            if self.df[column].dtype == float:
                self.info[column].update({'type':float})
                self.info[column].update(self.getFloatMetrics(self.df[column]))
            
            elif self.df[column].dtype == object:
                self.info[column].update({'type':object})
                self.info[column].update(self.getStringMetrics(self.df[column]))

            elif self.df[column].dtype == int:
                self.info[column].update({'type':int})
                self.info[column].update(self.getIntMetrics(self.df[column]))

            elif is_datetime(self.df[column]):
                self.info[column].update({'type':'timestamp'})
                self.info[column].update(self.getDatetimeMetrics(self.df[column]))
        f = open('log.txt', 'w')
        f.write(str(self.info))
        f.close()
        self.composeResult()

    def composeResult(self):
        df_info = pd.DataFrame([['rows: ', self.df_info['rows']],\
                                    ['columns: ', self.df_info['columns']]])
        df_columns = []

        for column in self.info:
            temp = pd.DataFrame([['column: ', str(column)]]+[[str(key), str(value)] for key,value in self.info[column].items()])
            temp['__white_space'] = ['']*temp.shape[0]
            df_columns.append(temp)

        df_columns = pd.concat(df_columns, axis=1, ignore_index=True)

        df = pd.concat([df_info, df_columns], ignore_index=True)

        df = df.fillna('')

        self.result_df = df

    def outputResult(self):
        if self.output_type == 'markdown':
            with open (self.out_filename, 'w') as f:
                f.write(self.result_df.to_markdown())
        elif self.output_type == 'html':
            with open (self.out_filename, 'w') as f:
                f.write(self.result_df.to_html())
        elif self.output_type == 'xlsx':
            self.result_df.to_excel(self.out_filename)


    def getFloatMetrics(self, df: pd.Series):
        metrics = dict()
        data = df.to_numpy()

        metrics.update({'min value' : np.min(data)})
        metrics.update({'max value' : np.max(data)})
        metrics.update({'mean value' : np.mean(data)})
        metrics.update({'median value' : np.median(data)})
        metrics.update({'proportion of zero rows' : np.count_nonzero(data==0)/data.shape[0]})
        metrics.update({'variance' : np.var(data)})
        metrics.update({'standard deviation' : np.std(data)})
        metrics.update({'interquartile range' : np.subtract(*np.percentile(data, [75, 25]))})
        a, b = stats.kstest(data, 'norm')
        metrics.update({'distribution normality by ks test' : 'normal' if b<0.05 else 'not normal'})

        return metrics # last minute catch: probably would've been better OOP with modifying an object field instead of returning and assigning result

    def getStringMetrics(self, df):
        metrics = dict()
        data = df.to_numpy()
        unique,pos = np.unique(data,return_inverse=True)
        counts = np.bincount(pos)
        maxpos = counts.argmax()

        metrics.update({'number of unique values' : len(set(data))})
        metrics.update({'most common value' : unique[maxpos]})
        metrics.update({'most common value occurances' : counts[maxpos]})

        return metrics

    def getIntMetrics(self, df):
        metrics = dict()
        data = df.to_numpy()
        uniques = set(data)
        metrics.update({'min value' : np.min(data)})
        metrics.update({'max value' : np.max(data)})
        metrics.update({'mean value' : np.mean(data)})
        metrics.update({'median value' : np.median(data)})
        metrics.update({'proportion of zero rows' : np.count_nonzero(data==0)/data.shape[0]})
        metrics.update({'variance' : np.var(data)})
        metrics.update({'standard deviation' : np.std(data)})
        metrics.update({'number of unique values' : len(uniques)})

        ascending = list(df) == sorted(list(df))
        descending = list(df) == sorted(list(df), reverse=True)
        if ascending:
            ordered = 'ascending'
        elif descending:
            ordered = 'descending'
        else:
            ordered = 'not ordered'
        metrics.update({'ordered' : ordered})

        uniques_sorted = sorted(list(uniques))
        distances = [a-b == 1 for a, b in zip(uniques_sorted[1:], uniques_sorted[:-1])]
        metrics.update({'density' : 'dense' if all(distances) else 'not dense'}) # checks for holes in natural (whole) numbers represented in a column

        return metrics

    def getDatetimeMetrics(self, df):
        metrics = dict()
        metrics.update({'earliest recorded time' : df.min().strftime("%m/%d/%Y, %H:%M:%S")})
        metrics.update({'latest recorded time' : df.max().strftime("%m/%d/%Y, %H:%M:%S")})
        metrics.update({'timespan' : str(df.max()-df.min())})
        metrics.update({'is time series in order' : 'in order' if list(df) == sorted(list(df)) else 'not in order'})

        # TO BE IMPLEMENTED: "dense" if all adjacent timestamps are equal timedelta apart (expecting irregularities with approximating nanoseconds)

        return metrics


def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help=".csv file with pandas dataframe to process", action = 'store', type = str)
    parser.add_argument('output_type', help="output type: markdown, html or xlsx", action = 'store', type = str)
    parser.add_argument('output_filename', help="file name for the ouput file", action = 'store', type = str)
    parser.add_argument('-dt', '--datetime_cols', help="names of datetime columns, comma-separated", action = 'store', type = str, required = False)
    args = parser.parse_args()
    table = TableHandler(args.input_file, args.output_type, args.output_filename, args.datetime_cols)
    table.parseDataset()
    table.outputResult()

if __name__ == '__main__':
    Main()