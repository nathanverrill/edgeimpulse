"""
Common helper functions for converting csv files into Edge Impulse compatible samples
"""

import pandas as pd
import numpy as np
import datetime, os, hashlib

def fill_missing_samples(df: pd.DataFrame) -> pd.DataFrame:
    """ Fill in any missing values in the dataframe with the last valid sample value
    """
    df = df.fillna(method='ffill')
    # Implementation note:
    #   Perform backfill pass after front fill in case the first N samples of a column are empty
    df = df.fillna(method='bfill')

    return df


def convert_datetime_format(df: pd.DataFrame, datetime_column_name: str) -> pd.DataFrame:
    """ Convert a supplied datetime column of a dataframe to an edge-impulse compatible numerical 
    timestamp column
    """
    # 1. Attempt to convert the supplied column to a datetime data type.
    #    This will fail if the format or column name is invalid
    datetimes = pd.to_datetime(df[datetime_column_name])

    # 2. Subtract all datetimes by the first sample datetime, giving a column of timedeltas (ns)
    start = datetimes.iloc[0]
    datetimes = datetimes - start

    # 3. Divide to get the millisecond timestamp as a float
    timestamps = datetimes / datetime.timedelta(milliseconds=1)

    # 4. Update the original dataframe with timestamp column
    df = df.drop(datetime_column_name, 1)
    df.insert(0, 'timestamp', timestamps) # insert is implicitly in-place
    return df


def remove_non_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """ Remove all non-numeric columns from the input dataframe, as only numeric values are allowed
    in edge impulse csv samples
    """
    df = df.select_dtypes(['number', np.number])
    return df

def sample_windows_from_event_log(
        df: pd.DataFrame,
        window_interval_ms: int,
        window_size_ms: int,
        label_column_name: str,
        save_directory: str,
        base_filename: str = "sample"):
    """ Create labelled sample windows from an 'event log', where labels are provided in a column
    at each timestamp. The windowed samples are created based on the window_interval_ms and 
    window_size_ms parameters, and csv files for each window are created in `save_directory` with 
    the naming convention: `label.base_filename.unique_hash.csv`. Edge Impulse can then parse the
    output csvs, and obtain the labels from the filenames

    Note: the event log must have an edge impulse compatible timestamp column (numeric, in milliseconds)
    """

    df = fill_missing_samples(df)

    # set the 'timestamp' column as index in order to use pandas index search tools
    df = df.set_index('timestamp')

    sample_count = df.shape[0]
    start_time = df.index[0]
    end_time = df.index[-1]
    window_start_loc = 0
    window_end_loc = 0
    while window_end_loc < sample_count and start_time < (end_time + window_size_ms):
        window_start_loc = df.index.get_loc(start_time, method='nearest')
        window_end_loc = df.index.get_loc(start_time + window_size_ms, method='nearest')

        start_time += window_interval_ms

        label = df[label_column_name].iloc[window_end_loc]
        window_df = df.iloc[window_start_loc:window_end_loc]
        window_df = remove_non_numeric_columns(window_df)

        csv_hash, csv_string = hash_dataframe(window_df)

        filename = label + '.' + base_filename + '.' + csv_hash + '.csv'
        print("creating sample {} at time {}/{}".format(filename, start_time, end_time))
        try:
            with open(os.path.join(save_directory, filename), 'xb') as f:
                f.write(csv_string)
        except:
            print("warning: duplicate filename in save_directory, likely a hash collision: ", filename)

def hash_dataframe(df: pd.DataFrame):
    """obtain a hash of a dataframe. Returns a tuple of the hash, and the csv_string of the 
    dataframe
    """
    # Implementation note:
    #   It's complicated to properly hash a dataframe, so here the csv is saved to a string
    #   and hashed directly before saving to a file
    csv_string = df.to_csv().encode('utf-8')
    csv_hash = hashlib.sha256(csv_string).hexdigest()
    return csv_hash, csv_string
