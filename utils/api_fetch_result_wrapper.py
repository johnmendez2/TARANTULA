import requests
import json
import time
from utils.api_llm_result import fetch_result 
def fetch_result_wrapper(user_id, requestId, taskId):
    # Define the maximum time to wait in seconds
    max_wait_time = 20
    
    # Start timing
    start_time = time.time()
    
    while True:
        # Call the original fetch_result function
        llm_response = fetch_result(user_id, requestId, taskId)
        
        # Check if llm_response is None
        if llm_response is None:
            print("Received a None response. Consider adding error handling or retry logic.")
            # Decide on the next action: continue waiting, break the loop, etc.
            # For demonstration, breaking the loop and returning None
            break
        
        # Since llm_response is already a dictionary, no need to parse it
        data = llm_response
        
        # Extract the error_code reason
        error_reason = data.get("errorCode", {}).get("reason", "Unknown")
        
        # Check if the error reason is "Success"
        if error_reason == "Success":
            print("Operation completed successfully.")
            return data
        
        # Check if the maximum wait time has been exceeded
        if time.time() - start_time > max_wait_time:
            print("Operation did not complete within the allowed time.")
            return data
        
        # Optionally, add a delay between retries
        time.sleep(1)

# # Example usage
# user_id = "your_user_id_here"
# requestId = "your_request_id_here"
# taskId = "799e8cd9-c5d6-491c-9e1d-255aae723a90"

# # Wrap the call to fetch_result with our new function
# data = fetch_result_wrapper(user_id, requestId, taskId)

# Now, data contains the response from the successful fetch or the last response if not successful within 20 seconds
