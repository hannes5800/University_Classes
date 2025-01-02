import nasdaqdatalink
import pandas as pd
import requests

def get_btc_data(codes=["TOTBC", "MKPRU", "ATRCT", "AVBLS", "BLCHS", "CPTRA", "CPTRV", "DIFF", "ETRAV", "ETRVU", "HRATE", "MIREV", "MKTCP", 
                        "MWNTD", "MWNUS", "MWTRV", "NADDU", "NTRAN", "NTRAT", "NTRBL", "NTREP", "TOUTV", "TRFEE", "TRFUS","TRVOU"]):
    """
    Fetch and organize Bitcoin blockchain data of the table "QDL/BCHAIN" (table code) from the Nasdaq Data Link API.
    Further information (e.g. for codes): https://data.nasdaq.com/databases/BCHAIN

    This function takes an iterable of codes (e.g., a list of strings), queries the Nasdaq Data Link table 'QDL/BCHAIN' 
    for each code, and returns a tidy Pandas DataFrame. Each code corresponds to a specific Bitcoin-related metric, 
    such as market price or hash rate.

    The resulting DataFrame will have:
      - A 'date' column.
      - Each code as a separate column with the corresponding values.

    Parameters:
    -----------
    codes : iterable of str
        An iterable containing the codes to query. Each code should be a valid metric code from the QDL/BCHAIN dataset.

    Returns:
    --------
    pd.DataFrame
        A tidy DataFrame with the 'date' column and the values of the queried codes as separate columns.

    Usage:
    ------
    Store your API key in a separate text file and let the function load it to keep it secure:

        with open('api_key.txt', 'r') as file:
            nasdaqdatalink.ApiConfig.api_key = file.read().strip()

    Example:
    --------
    >>> codes = ['MKPRU', 'HRATE', 'TRFEE']
    >>> df = fetch_and_tidy_bchain_data(codes)
    >>> print(df)

    Security Note:
    --------------
    Always keep your API key private and avoid sharing or exposing it in public code repositories. 
    This function assumes your API key is stored in the local repository in 'nasdaq_data_link_API.txt'. 
    
    """
    # Load API key from file
    with open('nasdaq_data_link_API.txt', 'r') as file:
        nasdaqdatalink.ApiConfig.api_key = file.read().strip()

    data_frames = []  # List to hold individual DataFrames
    
    for code in codes:
        # Fetch data for the given code
        response = nasdaqdatalink.get_table('QDL/BCHAIN', code=code)

        # Select and rename columns
        df = response[['date', 'value']].copy()
        df.rename(columns={'value': code}, inplace=True)

        # Append to the list of DataFrames
        data_frames.append(df)

    # Merge all DataFrames on the 'date' column using an outer join
    merged_df = data_frames[0]
    for df in data_frames[1:]:
        merged_df = pd.merge(merged_df, df, on='date', how='outer')
    
    # Switch merged DataFrame, so the earliest date is the first row
    # Also exclude last row, which cotains current day (data will change until the day ends)
    merged_df.sort_values(by=['date'], inplace=True)
    merged_df.drop(merged_df.tail(1).index, inplace=True)

    # Write data to CSV and return the data:
    csv_filename = "nasdaq-data-BTC.csv"
    merged_df.to_csv(csv_filename)
    return merged_df


def get_btc_table_metadata():
    with open('nasdaq_data_link_API.txt', 'r') as file:
        nasdaq_api = file.read().strip()
    metadata_json = requests.get(f"https://data.nasdaq.com/api/v3/datatables/QDL/BCHAIN/metadata?api_key={nasdaq_api}").json()
    return metadata_json
