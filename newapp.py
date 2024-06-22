from flask import Flask, request, jsonify, Response
import json
import time
import threading
import requests
import uuid
import datetime
import os
import json
from dotenv import load_dotenv
from utils.version import API_VERSION, SERVICE_NAME
from utils.status_codes import StatusCodes
from uuid import uuid4
from api.models import response_template
import re
from flask_swagger_ui import get_swaggerui_blueprint
from utils.s3_presign import create_presigned_url
from utils.s3_create_folder import create_folder
from utils.s3_delete_object import generate_presigned_delete
from utils.s3_copy_object import generate_presigned_copy
from utils.s3_rename_presigned import rename_and_delete_old_s3_file
from utils.s3_fetch_file import chosen_files
from utils.s3_get_total_size import calculate_total_folder_size
from utils.s3_get_project_structure import list_directory_paths
from utils.api_llm_result import fetch_result
# from utils.api_call_llm import send_completion_request
from utils.api_fetch_result_wrapper import fetch_result_wrapper
from flask_cors import CORS
app = Flask(__name__)
# Load environment variables
load_dotenv(override=True)
app.config.from_object(__name__)  # Load config from object
CORS(app)
# Load JSON configuration
with open('config.json') as f:
    config = json.load(f)

# Now you can access your configuration values like this:
debug_mode = app.config['DEBUG']

############### SWAGGER DOCUMENTATION ###############

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
cwd = os.getcwd()
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)
# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "TARANTULA WEBSITE BUILDER"
    },
)

app.register_blueprint(swaggerui_blueprint)

############### ENV VARIABLES ###############
SUPPORTED_METHOD = ["write_code", "make_changes","upload_project", "edit_object", "download_project", "get_directory_structure", "get_project_size", "get_file"]


############### ADD YOUR AI MARKETPLACE WEBHOOK ENDPOINT HERE ###############
# webhook_url = "http://localhost:8000/callback"
webhook_url = "https://marketplace-api-user.dev.devsaitech.com/api/v1/ai-connection/callback"

############### ADD YOUR CUSTOM AI AGENT CALL HERE ###############


############### GLOBAL PROMPT TEMPLATES ###############
update = """
UPDATE src/App.js
```javascript
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Example from "./Example.js";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
          <Route path="/" element={<Example/>} />
      </Routes>
    </BrowserRouter>
  );
}
```
"""

create = """
CREATE src/Component.css
```css

```
"""


WebWriter ="""
Your name is Tarantula, you are a full-stack ReactJS developer developed by SOLIDUS AITECH. You will only respond to Web Development questions.\
You will help update existing components and create new components based on the users requirements.\
Here is the users src/App.js file:
{code_snippet}

You must update App.js to import any components that are necessary. You must import CSS for the respective javascript files.
You must implement every function yourself, do not leave any tasks for the user.\
Only use libraries you are sure of, do not use libraries that do not exist, or that aren't popular.\
If you need to use a library that is not imported in the code, send a bash command to install the library in the form "npm install".\
If you are sending code, send the whole code along with updates. Do not ever say // ... (rest of the component) or there will be severe consequences, ensure you send the whole codebase along with the component and JSX.\
You must cite the appropriate component operation and name every time you send code without fail using the prefix "CREATE src/Component.js" or "UPDATE src/Component.js" before a code snippet. Some examples are as follows:
{update}

{create}

Ensure that the operation name prefixes are always present before sending the code snippet or there will be severe consequences.
"""

CodeSpinner = f"""
You are CodeSpinner, an agent that updates old Components with the updates mentioned to you. You will respond with the entire component updated with the changes provided to you.\
You must rewrite the entire file in your response and never use // ... rest of the component. Failure to listen to this instruction will cause grave consequences.\
You must cite the appropriate component operation and name every time you send code without fail using the prefix "CREATE src/Component.js" or "UPDATE src/Component.js" before a code snippet. Some examples are as follows:
{update}

CREATE src/Component.css
```css

```
"""

############### MAIN FUNCTIONS ###############

import requests

def send_completion_request(requestID, userID, systemmessage, userquery):
    """
    Sends a completion request to the specified endpoint.

    Parameters:
    requestID (str): The unique request ID.
    userID (str): The user ID making the request.
    systemmessage (str): The system message to include in the request.
    userquery (str): The user query to include in the request.

    Returns:
    response: The response from the server if successful, otherwise the status code or exception.
    """
    # Define the URL for the request
    url = 'http://ec2-54-251-99-208.ap-southeast-1.compute.amazonaws.com:8010/call'

    # Define the headers as per the curl command
    headers = {
        'x-marketplace-token': '1df239ef34d92aa8190b8086e89196ce41ce364190262ba71964e9f84112bc45',
        'x-request-id': str(requestID),
        'x-user-id': str(userID),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Define the payload
    payload = {
        "method": "completion",
        "payload": {
            "model": "llama3_70b",
            "messages": [
                {
                    "role": "system",
                    "content": str(systemmessage)
                },
                {
                    "role": "user",
                    "content": str(userquery)
                }
            ],
            "temperature": 0.0,
            "topP": 0.55,
            "maxTokens": 4096
        }
    }

    print(payload)

    # Send the POST request
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Request successfuly sent.")
            # Print the response JSON
            print(response.json())
            return response
        else:
            print(f"Request failed with status code {response.status_code}.")
            print(response.text)  # Print the error message from the server
            return response.status_code
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return e

def generate(user_id, request):
    global WebWriter
    global CodeSpinner 
    # print(request)
    requestId = str(uuid.uuid4())
    file_paths = request.get('payload').get('file_paths')
    query_string = request.get('payload').get('query_string')  # Extract the query string from the request
    agent = request.get('payload').get('agent') # Assuming 'agent' is passed in the request
    webwriterresponse = request.get('payload').get('webwriterresponse')  # Assuming 'agent' is passed in the request
    project = request.get('payload').get('project_name')  # Assuming 'agent' is passed in the request

    # print(f"query string: {query_string}")
    # file_paths = request.json.get('filePaths') # Get the S3 file's from user that they want to change
    # Extracting 'method'
    method = request['method']
    # print(method)  # Output: example_method
    if method == "write_code":
        file_loc = ""
        if agent:
            if file_paths:
                file_loc = chosen_files(user_id, project, file_paths)
            elif agent != "CodeSpinner":
                file_loc = ""


        app_js = chosen_files(user_id, project, ["App.js"])
        print("appjs: "+app_js)
        if "No files" in app_js:
            return "No files found in that project"
        query_str = f'''{query_string}\n{file_loc}'''
        # print(f"file_loc : {file_loc}")
        WebWriter_formatted = WebWriter.format(code_snippet=app_js, update=update, create=create)
        # prompt_template = f'''###Sytem Message:\n{WebWriter}\n\n### User Query:\nYou must state the appropriate "npm install" commands if you use any npm libraries in your response. You must cite without fail the appropriate component using the prefix "CREATE src/Component.js" or "UPDATE src/Component.js" before a code snippet. Some examples are as follows:\nUPDATE src/App.js\n```javascript\n\n```\n\nCREATE src/Component.js\n```javascript\n\n```\n{query_str}\n\n### System Response:'''                 
        prompt_template = f'''###Sytem Message:\n{WebWriter_formatted}\n\n### User Query:\nYou must state the appropriate "npm install" commands if you use any npm libraries in your response. You must cite without fail the appropriate component using the prefix "CREATE src/Component.js" or "UPDATE src/Component.js" before a code snippet. Some examples are as follows:\nUPDATE src/App.js\n```javascript\n\n```\n\nCREATE src/Component.js\n```javascript\n\n```\n{query_str}\n\n### System Response:'''                 
        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": query_string}
        ]  
        completion_response = send_completion_request(user_id, requestId, str(prompt_template), str(query_string))
        # Load the JSON string into a Python dictionary
        # Assuming completion_response is a Response object from the requests library
        try:
            data = completion_response.json()  # Use.json() method to parse the JSON content
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


        # # Extract the taskId
        taskId = data['response']['taskId']
        print(taskId)
        # data = fetch_result_wrapper(user_id, requestId, taskId)
        if taskId != "":
            data = taskId
        else:
            data = data['errorCode']['reason']
        # data = "Example response"
        print(str(data))
        # data = "This is an example response."
        # Return the initial data
        return str(data)
    
    elif method == "make_changes":
        # Regex pattern to match the file names after "UPDATE ", capturing everything after the last slash
        pattern = r"UPDATE\s+.*?/(.*?)\n"
        webwriterresponse = request.get('payload').get('webwriterresponse')  # Assuming 'agent' is passed in the request

        # Find all matches
        file_names = re.findall(pattern, webwriterresponse)

        # Print the extracted file names
        for file_name in file_names:
            print(f"file name : {file_name}")

        file_loc = ""
        if file_names != []:
            file_loc = chosen_files(user_id, project, file_names)
        elif agent != "CodeSpinner":
            file_loc = ""

        print("file_loc: "+file_loc)
        if "No files" in file_loc:
            return "No files found in that project"

        if file_loc != "":
            prompt_template = f'''Original code files:\n{file_loc}\n\n### Find and update the code using the appropriate operations "CREATE" and "UPDATE" that you must incorporate in the existing code:\n{webwriterresponse}\n### CodeSpinner Response:\n'''            
        else:
            prompt_template = f'''### Find and update the code using the appropriate operations "CREATE" and "UPDATE" that you must incorporate in the existing code:\n{webwriterresponse}\n### CodeSpinner Response:\n'''            

        messages = [
            {"role": "system", "content": CodeSpinner},
            {"role": "user", "content": prompt_template}
        ]  
        completion_response = send_completion_request(user_id, requestId, CodeSpinner, prompt_template)
        # Load the JSON string into a Python dictionary
        # Assuming completion_response is a Response object from the requests library
        try:
            data = completion_response.json()  # Use.json() method to parse the JSON content
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


        # # Extract the taskId
        taskId = data['response']['taskId']
        print(taskId)
        # data = fetch_result_wrapper(user_id, requestId, taskId)
        if taskId != "":
            data = taskId
        else:
            data = data['errorCode']['reason']
        # data = "Example response"
        print(str(data))
        # data = "This is an example response."
        # Return the initial data
        print(user_id)
        print(requestId)
        return str(data)
    
############### MIDDLEWARE FUNCTIONS ###############
# Modify the return statement in process_query to handle generator functions correctly
def process_query(user_id, request_data):
    start_time = time.time()
    collected_data = generate(user_id, request_data)
    print (f"response_data = {collected_data}")
    # Now, collected_data contains all the data yielded by the generate function
    # You can proceed with your logic to return these data as needed
    # For example, return them as part of a JSON response
    end_time = time.time()
    processing_duration = end_time - start_time  # Calculate processing duration in seconds
    return collected_data, processing_duration

def success_response(task_id, data, requestId, trace_id, process_duration):
        # Prepare the response
        response = {
            "taskId": task_id,  # Assuming task_id is defined somewhere
            "data": data,
            "dataType": "S3_OBJECT"
        }
        error_code = {"status": StatusCodes.SUCCESS, "reason": "success"}
        response_data = response_template(requestId, trace_id, process_duration, True, response, error_code)
        return response_data

############### CHECK IF ALL INFORMATION IS IN REQUEST ###############
def check_input_request(request):
    reason = ""
    status = ""
    request_data = request.get_json()
    file_paths = request_data.get('payload').get('file_paths')
    query_string = request_data.get('payload').get('query_string')  # Extract the query string from the request
    agent = request_data.get('payload').get('agent') # Assuming 'agent' is passed in the request
    webwriterresponse = request_data.get('payload').get('webwriterresponse')  # Assuming 'agent' is passed in the request
    project = request_data.get('payload').get('project_name')
    user_id = request.headers.get('X-User-ID', None)

    if user_id is None or not user_id.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "userToken is invalid"
    request_id = request.headers.get('x-request-id', None)
    request_data = request.get_json()
    print(request_data)
    respose_data = None

    if project is None or not project.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "project_name field is invalid/not found"
    request_id = request.headers.get('x-request-id', None)
    request_data = request.get_json()
    print(request_data)
    respose_data = None

    method = request_data['method']
    print(method)

    if request_id is None or not request_id.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "requestId is invalid"
    if method is None or not method.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "Method is invalid"
    elif method not in SUPPORTED_METHOD:
        status = StatusCodes.UNSUPPORTED
        reason = f"Unsupported method {method}"
    if file_paths:
        if not isinstance(file_paths, list):
            status = StatusCodes.INVALID_REQUEST
            reason = f"Invalid file paths {file_paths}"
    if agent == "CodeSpinner":
        if webwriterresponse is None or not webwriterresponse.strip():
            status = StatusCodes.INVALID_REQUEST
            reason = "Last WebWriter response is not found"
    if agent == "WebWriter":
        if query_string is None or not query_string.strip():
            status = StatusCodes.INVALID_REQUEST
            reason = "Query string not found"
    if agent is None or not agent.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "Agent type not found"

    if status != "":
        trace_id = uuid4().hex
        error_code = {
            "status": status,
            "reason": reason
        }
    
        respose_data = response_template(request_id, trace_id, -1,True,{}, error_code)
        
    return respose_data


############### API ENDPOINT TO RECEIVE REQUEST ###############
@app.route('/call', methods=['POST'])
def call_endpoint():
    user_id = request.headers.get('X-User-ID', None)

    request_data = request.get_json()
    task_id = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    method = request_data['method']
    structures = request_data.get('payload').get('structures')
    project_name = request_data.get('payload').get('project_name')

    if method == "get_file":
        project = request_data.get('payload').get('project_name')
        file_paths = request_data.get('payload').get('file_paths')
        file = chosen_files(user_id, project, file_paths)
        response_data = success_response(task_id, file, requestId, trace_id, 1)
        return response_data

    if method == "upload_project":
        if user_id is not None and structures is not None and project_name is not None:
            folder_path = f"{user_id}/"
            folder_response,folder_bool = create_folder(folder_path)
            if folder_bool:
                start_time = time.time()
                request_data = request.get_json()
                project_path = folder_path + project_name +'/'
                
                # Adjusting the pre_signed_urls generation to include folder_path as a prefix
                pre_signed_urls = {project_path + file: create_presigned_url(project_path + file) for file in structures}
                data =  {
                    "folder_status": folder_response,
                    "pre_signed_urls": pre_signed_urls
                }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data
            else:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": f"Folder cannot be created due to: {folder_response}."}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
        else:
            if project_name is None:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "Cannot find project name in payload"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
            if structures is None:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "Structures array not found in payload"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
            else:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "User ID not found"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
        


    if method == "edit_object":
        if user_id is not None:
            folder_path = f"{user_id}/"
            request_data = request.get_json()
            path = request_data.get('payload').get('path')
            edit_method = request_data.get('payload').get('method')
            type = request_data.get('payload').get('type')
            old_file_path = request_data.get('payload').get('old_file_path')
            new_file_path = request_data.get('payload').get('new_file_path')
            paths_list = request_data.get('payload').get('paths')

            if edit_method == "CREATE" and not path is None:
                start_time = time.time()
                file_path = folder_path + path
                new_file_presigned = create_presigned_url(file_path) 
                data = {
                        "type": type,
                        "data": new_file_presigned
                    }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data

            if edit_method == "WRITE" and not path is None:
                start_time = time.time()
                file_path = folder_path + path
                file_presigned = create_presigned_url(file_path) 
                data = {
                        "type": type,
                        "data": file_presigned
                    }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data
            
            if edit_method == "DELETE" and not path is None:
                start_time = time.time()
                file_path = folder_path + path
                file_presigned = generate_presigned_delete(file_path) 
                data =  {
                        "type": type,
                        "data": file_presigned
                    }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data
            

            if edit_method == "RENAME":

                if type == "FILE" and not old_file_path is None and not new_file_path is None:
                    start_time = time.time()
                    result = rename_and_delete_old_s3_file(old_file_path, new_file_path)
                    print(result)
                    if result == "New file copied succesfully. Old file deleted successfully.":
                        data = {
                                "type": type,
                                "response": result
                        }
                        end_time = time.time()
                        process_duration = end_time - start_time
                        response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                        return response_data
                    else:
                        response = {
                            "taskId": task_id,  # Assuming task_id is defined somewhere
                            "data": {}
                        }
                        error_code = {"status": StatusCodes.ERROR, "reason": result}
                        response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                        return response_data

                if type == "FOLDER" and not paths_list is None:
                    start_time = time.time()
                    successful_operations = []  # List to store successful operations
                    failed_operations = []  # List to store failed operations
                    # Parse the JSON string into a Python object (a list of dictionaries in this case)
                    parsed_paths_list = json.loads(paths_list)
                    for path_item in parsed_paths_list:
                        old_path = path_item["old_file_path"]
                        new_path = path_item["new_file_path"]
                        rename_result = rename_and_delete_old_s3_file(old_path, new_path)  # Assuming you have a similar function for folders
                        print(rename_result)
                        if rename_result == "New file copied succesfully. Old file deleted successfully.":
                            successful_operations.append({
                                "oldPath": old_path,
                                "newPath": new_path,
                                "status": "Success",
                                "message": rename_result
                            })
                        else:
                            failed_operations.append({
                                "oldPath": old_path,
                                "newPath": new_path,
                                "status": "Error",
                                "message": rename_result
                            })

                    # Constructing the final response
                    if successful_operations:
                        data = {
                                "type": type,
                                "successfulOperations": successful_operations,
                                "failedOperations": failed_operations
                            }
                        end_time = time.time()
                        process_duration = end_time - start_time
                        response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                        return response_data
                    else:
                        response = {
                            "taskId": task_id,  # Assuming task_id is defined somewhere
                            "data": {
                                "type": type,
                                "failedOperations": failed_operations
                            }
                        }
                        error_code = {"status": StatusCodes.ERROR, "reason": "All operations failed"}
                        response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                        return response_data
                else:
                    response = {}
                    error_code = {"status": StatusCodes.ERROR, "reason": "Payload items missing"}
                    response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                    return response_data

            else:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "Wrong method type / missing payload"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data

        else:
            response = {}
            error_code = {"status": StatusCodes.ERROR, "reason": "User ID not found"}
            response_data = response_template(requestId, trace_id, -1, True, response, error_code)
            return response_data
        
    if method == "get_directory_structure":
        if user_id is not None:
            start_time = time.time()
            request_data = request.get_json()
            project_name = request_data.get('payload').get('project_name')
            if project_name is not None:
                structure = list_directory_paths(user_id, project_name)
                data = {
                        "data": structure
                }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data
            else:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "Project name not found"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
        else:
            response = {}
            error_code = {"status": StatusCodes.ERROR, "reason": "User ID not found"}
            response_data = response_template(requestId, trace_id, -1, True, response, error_code)
            return response_data
        


    if method == "get_project_size":
        if user_id is not None:
            start_time = time.time()
            request_data = request.get_json()
            project_name = request_data.get('payload').get('project_name')
            if project_name is not None:
                size = calculate_total_folder_size(user_id, project_name)
                data = {
                        "project_size": size
                }
                end_time = time.time()
                process_duration = end_time - start_time
                response_data = success_response(task_id, data, requestId, trace_id, process_duration)
                return response_data
            else:
                response = {}
                error_code = {"status": StatusCodes.ERROR, "reason": "Project name not found"}
                response_data = response_template(requestId, trace_id, -1, True, response, error_code)
                return response_data
        else:
            response = {}
            error_code = {"status": StatusCodes.ERROR, "reason": "User ID not found"}
            response_data = response_template(requestId, trace_id, -1, True, response, error_code)
            return response_data

    else:
        # Database insertion
        ret = check_input_request(request)
        if ret is not None:
            return ret

        # Response preparation
        task_status, processing_duration = process_task(task_id,requestId, user_id, request_data)

        if "No files" in task_status:
            error_code = {"status": StatusCodes.ERROR, "reason": "No files found in the project"}
            response_data = response_template(requestId, trace_id, -1, True, task_status, error_code)
            return response_data

        print(task_status)
        response = {"taskId": task_status}
        error_code = {"status": StatusCodes.PENDING, "reason": "Pending"}
        respose_data = response_template(requestId, trace_id, processing_duration, False, response, error_code)
        # task_status = process_task(task_id,requestId, user_id, request_data)
        # Immediate response to the client
        return jsonify(respose_data), 200
    
@app.route('/result', methods=['POST'])
def result():
    user_id = request.headers.get('X-User-ID', None)
    requestId = request.headers.get('x-request-id', None)
    request_data = request.get_json()
    taskID = request_data.get("taskId")
    trace_id = str(uuid.uuid4())
    result_request_id = str(uuid.uuid4())
    if user_id is None or not user_id.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No User ID found in headers"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data

    if requestId is None or not requestId.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No request ID found in headers"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data
    
    if taskID is None or not taskID.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No task ID found in body"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data

    print(taskID)
    data = fetch_result(user_id, requestId, taskID)
    print(data)
    return jsonify(data), 200


############### PROCESS THE CALL TASK HERE ###############
def process_task(task_id,requestId, user_id,request_data):
    data, processing_duration = process_query(user_id,request_data)
    print(data)
    # Send the callback
    # callback = send_callback(task_id,processing_duration, data)
    return data, processing_duration

############### SEND CALLBACK TO YOUR APP MARKETPLACE ENDPOINT WITH TASK RESPONSE ###############
def send_callback(task_id, processing_duration, data):
    
    callback_message = {
        "apiVersion": API_VERSION,
        "service": SERVICE_NAME,
        "datetime": datetime.datetime.now().isoformat(),
        "processDuration": processing_duration,  # Simulated duration
        "taskId": task_id,
        "isResponseImmediate": True,
        "response": {
            "dataType": "META_DATA",
            "data": data
        },
        "errorCode": {
            "status": "TA_000",
            "reason": "success"
        }
    }
    # return callback_message
    return callback_message

############### RUN YOUR SERVER HERE ###############
if __name__ == '__main__':
    app.run(debug=True)