import requests

def send_completion_request(requestID, userID, systemmessage, userquery):
    # Define the URL for the request
    url = 'http://ec2-13-212-114-8.ap-southeast-1.compute.amazonaws.com:8010/call'

    # Define the headers as per the curl command
    headers = {
        'x-marketplace-token': '1df239ef34d92aa8190b8086e89196ce41ce364190262ba71964e9f84112bc45',
        'x-request-id': requestID,
        'x-user-id': userID,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Define the payload
    payload = {
        "method": "completion",
        "payload": {
            "model": "mistral7b",
            "messages": [
                {
                    "role": "system",
                    "content": systemmessage
                },
                {
                    "role": "user",
                    "content": userquery
                }
            ],
            "temperature": 0.0,
            "topP": 0.95,
            "maxTokens": 128
        }
    }

    # Send the POST request
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful.")
            # Print the response text
            print(response.json())
            return response
        else:
            print(f"Request failed with status code {response.status_code}.")
            return response.status_code
    except Exception as e:
        print(f"An error occurred: {e}")
        return e

# # Call the function to execute the request
# send_completion_request("abc123", "abc123", "you are a helpful assistant", "hi what is the capital of USA")
