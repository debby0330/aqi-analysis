import os
import requests
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

api_key = os.getenv('AQI_API_KEY')
api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"

params = {
    'api_key': api_key,
    'format': 'json',
    'limit': 5
}

print(f"API Key: {api_key}")
print(f"URL: {api_url}")

try:
    response = requests.get(api_url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Data Type: {type(data)}")
        
        if isinstance(data, list):
            print(f"List Length: {len(data)}")
            if data:
                print(f"First Item Keys: {list(data[0].keys())}")
                print(f"First Item: {data[0]}")
        elif isinstance(data, dict):
            print(f"Dict Keys: {list(data.keys())}")
            if 'value' in data:
                print(f"Value Length: {len(data['value'])}")
                print(f"First Item Keys: {list(data['value'][0].keys()) if data['value'] else 'No data'}")
        else:
            print(f"Unexpected data type: {type(data)}")
            print(f"Full Response: {data}")
    else:
        print(f"Error Response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
