import pandas as pd 
import requests
import time
from datetime import datetime, timezone

# Function to fetch Bitcoin data from CryptoCompare
def get_asset_price_data(symbol='BTC', from_date='2009-09-01', to_date=None):
    """
    Fetch historical price data of a cryptocurrency fromCryptoCompare.

    Parameters:
        symbol (str): Symbol of the cryptocurrency (e.g., "BTC" for Bitcoin).
        from_date (str): Start date for fetching data in "YYYY-MM-DD" format (default: "2010-07-17").
        to_date (str): End date for fetching data in "YYYY-MM-DD" format (default: current date).

    Returns:
        DataFrame: Historical Bitcoin price data with time as the index.
    """
    with open('crypto_compare_API.txt', 'r') as file:
        crypto_compare_api = file.read().strip()
    url = f"https://min-api.cryptocompare.com/data/v2/histoday"
    all_data = []
    
    # Convert start_date and end_date first to datetime and then to int timestamps:
    # Note: variables are already named *_timestamp here because they will be converted to timestamps later and I want to keep the input parameters
    start_timestamp = int(datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc).timestamp())
    if to_date is None:
        end_timestamp = int(datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                        ).timestamp())-1
    else:
        end_timestamp = int(datetime.fromisoformat(to_date).replace(
                        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                        ).timestamp())-1
        
    # API headers
    headers = {
        "authorization": f"Apikey {crypto_compare_api}"
    }
    
    # Loop until the start date is reached:
    while end_timestamp > start_timestamp:
        # Calculate the start of the range (2000 days before the current end timestamp)
        range_start = end_timestamp - (2001 * 86400) + 1   # Start at 00:00:00 of the range
        range_start = max(range_start, start_timestamp)  # Ensure range_start doesn't go below start_timestamp
        
        # Prepare API parameters
        params = {
            'fsym': symbol, # From Symbol (default Bitcoin)
            'tsym': 'USD',  # To Symbol (US Dollar)
            'limit': 2000,  # Max number of data points per request
            'toTs': end_timestamp,
            'fromTs': range_start
        }
        
        # Make the API request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Prepend the data (earlier data at at the beginning)
            all_data = data['Data']['Data'] + all_data
            
            # Update the end_timestamp for the NEXT iteration to one second before the current start_timestamp
            end_timestamp = all_data[0]['time'] - 1  # Move to the previous range
        else:
            print(f"Error fetching data: {response.status_code}")
            break
        
        # Wait to avoid hitting rate limits:
        time.sleep(1)
    
    # Convert the collected data into a DataFrame and do some optimizations:
    df = pd.DataFrame(all_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime
    #df.set_index('time', inplace=True)  # Set 'time' as the index of the DataFrame
    #df.reset_index(inplace=True, drop=True)
    df.rename(columns={'time':'date'}, inplace=True)
    df = df[df.date >= from_date]
    df.reset_index(inplace=True, drop=True)

    # Write data to CSV and return the data:
    csv_filename = f"cc-price-data-{symbol}.csv"
    df.to_csv(csv_filename)
    return df




def get_daily_exchange_volume(symbol='BTC', tsym='USD', exchange='Coinbase', from_date='2009-09-01', to_date=None):
    """
    Fetch historical exchange volume data for a specific cryptocurrency from CryptoCompare.

    Parameters:
        symbol (str): Symbol of the cryptocurrency (e.g., "BTC" for Bitcoin).
        tysm (str): Base fiat currency to measure the metrics in (e.g., "USD" for US Dollar).
        exchange (str): Name of the exchange (e.g., "Coinbase" or "Binance").
        from_date (str): Start date for fetching data in "YYYY-MM-DD" format.
        to_date (str): End date for fetching data in "YYYY-MM-DD" format (default: current date).

    Returns:
        DataFrame: Historical exchange volume data with time as the index.
    """
    with open('crypto_compare_API.txt', 'r') as file:
        crypto_compare_api = file.read().strip()
    url = f"https://min-api.cryptocompare.com/data/exchange/symbol/histoday"
    all_data = []

    # Convert from_date and to_date to datetime objects and UTC timestamps
    start_timestamp = int(datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc).timestamp())
    if to_date is None:
        end_timestamp = int(datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                        ).timestamp())-1
    else:
        end_timestamp = int(datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc).timestamp())-1

    # API headers
    headers = {
        "authorization": f"Apikey {crypto_compare_api}"
    }

    # Loop until the start date is reached
    while end_timestamp >= start_timestamp:
        # Calculate the start of the range
        range_start = end_timestamp - (2001 * 86400) + 1
        range_start = max(range_start, start_timestamp)

        # Prepare API parameters
        params = {
            'fsym': symbol,  # From Symbol (Bitcoin)
            'tsym': tsym,  # To Symbol (US Dollar)
            'limit': 2000, # Max number of data points per request
            'toTs': end_timestamp,
            'e': exchange   # Exchange name
        }

        # Make the API request
        response = requests.get(url, params=params, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if 'Data' in data:
                # Prepend the data (earlier data at the beginning)
                all_data = data['Data'] + all_data

                # Update the end_timestamp for the next iteration
                end_timestamp = data['Data'][0]['time'] - 1
            else:
                print("No data available in response.")
                break
        else:
            print(f"Error fetching data: {response.status_code}")
            break

        # Wait to avoid hitting rate limits
        time.sleep(1)

    # Convert the collected data into a DataFrame and optimize
    df = pd.DataFrame(all_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime
    df.rename(columns={'time': 'date', 'volumeto': 'volume_to', 'volumefrom': 'volume_from', 'volumetotal': 'volume_total'}, inplace=True)
    df = df[df['date'] >= from_date]  # Filter rows within the requested date range
    df.reset_index(drop=True, inplace=True)

    # Save to CSV and return the data
    csv_filename = f"cc-exchange-volume-{exchange}.csv"
    df.to_csv(csv_filename)
    return df



def get_blockchain_info(symbol="BTC", from_date="2009-09-01", to_date=None, metrics=None):
    """
    Fetch historical daily active address data for a specific cryptocurrency from CryptoCompare.

    Parameters:
        symbol (str): Symbol of the cryptocurrency (e.g., "BTC" for Bitcoin).
        from_date (str): Start date for fetching data in "YYYY-MM-DD" format.
        to_date (str): End date for fetching data in "YYYY-MM-DD" format (default: current date).
        metrics (iterable of str): An iterable containing the metrics to query. If none, all metrics are queried.

    Returns:
        DataFrame: Historical daily active address data with time as the index.
    """
    with open('crypto_compare_API.txt', 'r') as file:
        crypto_compare_api = file.read().strip()
    url = f"https://min-api.cryptocompare.com/data/blockchain/histo/day"
    all_data = []

    # Convert from_date and to_date to datetime objects and UTC timestamps
    start_timestamp = int(datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc).timestamp())
    if to_date is None:
        end_timestamp = int(datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                        ).timestamp()) - 1
    else:
        end_timestamp = int(datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc).timestamp()) - 1

    # API headers
    headers = {
        "authorization": f"Apikey {crypto_compare_api}"
    }

    # Loop until the start date is reached
    while end_timestamp >= start_timestamp:
        # Calculate the start of the range
        range_start = end_timestamp - (2001 * 86400) + 1
        range_start = max(range_start, start_timestamp)

        # Prepare API parameters
        params = {
            'fsym': symbol,  # From Symbol (e.g., BTC for Bitcoin)
            'limit': 2000,   # Max number of data points per request
            'toTs': end_timestamp
        }

        # Make the API request
        response = requests.get(url, params=params, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if 'Data' in data and 'Data' in data['Data']:
                # Extract the list of data entries
                entries = data['Data']['Data']
                if isinstance(entries, list):
                    all_data = entries + all_data
                    # Update the end_timestamp for the next iteration
                    end_timestamp = entries[0]['time'] - 1
                else:
                    print("No data entries available.")
                    break
            else:
                print("No data available in response.")
                break

        # Wait to avoid hitting rate limits
        time.sleep(1)

    # Convert the collected data into a DataFrame and optimize
    df = pd.DataFrame(all_data)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime
    df.rename(columns={'time': 'date'}, inplace=True)
    df = df[df['date'] >= from_date]  # Filter rows within the requested date range
    df.reset_index(drop=True, inplace=True)

    # Calculate the total number of addresses
    total_addresses = []

    for index, row in df.iterrows():
        if index == 0:
            # For the first row, use 'unique_addresses_all_time' as 'total_addresses'
            total_addresses.append(row['unique_addresses_all_time'])
        else:
            # For subsequent rows, calculate total_addresses as:
            # total_addresses = previous_total_addresses + new_addresses
            previous_total = total_addresses[-1]
            total_addresses.append(previous_total + row['new_addresses'])
    
    # Add the calculated 'total_addresses' to the DataFrame
    df.insert(7, column='total_addresses_all_time', value=total_addresses)
    # If metrics is None return whole table, else just return the table where column names = metrics
    if metrics is None:
        df = df
    else:
        df = df[metrics]

    # Save to CSV and return the data
    csv_filename = f"cc-blockchain-info-{symbol}.csv"
    df.to_csv(csv_filename, index=False)
    return df
