import requests

# URL of the web service endpoint
url = "https://signals-db-234640427180.europe-central2.run.app/get_active_signals"

# Send GET request to the endpoint
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Schema retrieved successfully:")
    print(response.text)  # Print the response body, which is the schema
else:
    print(f"Failed to retrieve schema. Status code: {response.status_code}")
    print(response.text)  # Print the error message if any
