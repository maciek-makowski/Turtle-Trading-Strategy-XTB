import requests

# URL of the web service endpoint
URL = "https://signals-db-234640427180.europe-central2.run.app/"


def flush_db():
    response = requests.post(URL + "/flush_database")

    print("Status Code:", response.status_code) 
    print("Response JSON:", response.json())
    return response.json()

flush_db()
