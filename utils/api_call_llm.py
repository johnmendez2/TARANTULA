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
        'x-request-id': requestID,
        'x-user-id': userID,
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
                    "content": systemmessage
                },
                {
                    "role": "user",
                    "content": userquery
                }
            ],
            "temperature": 0.0,
            "topP": 0.55,
            "maxTokens": 4096
        }
    }

    # Send the POST request
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful.")
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

# CodeSpinner = """
# You are CodeSpinner, an agent that updates old Components with the updates mentioned to you. You will respond with the entire component updated with the changes provided to you.You must rewrite the entire file in your response and never use // ... rest of the component. Failure to listen to this instruction will cause grave consequences.You must cite the appropriate component operation and name every time you send code without fail using the prefix "CREATE src/Component.js" or "UPDATE src/Component.js" before a code snippet. Some examples are as follows:

# UPDATE src/App.js
# ```javascript
# import ReactDOM from "react-dom/client";
# import { BrowserRouter, Routes, Route } from "react-router-dom";
# import Example from "./Example.js";

# export default function App() {
#   return (
#     <BrowserRouter>
#       <Routes>
#           <Route path="/" element={<Example/>} />
#       </Routes>
#     </BrowserRouter>
#   );
# }
# ```



# CREATE src/Component.css
# ```css

# ```
# """

# prompt_template = """Original code files:
# sk-131r4qdad421451/welcomeapp/src/App.tsx:
# function App() {
# return (
#   <div>
#     Welcome to AITech
#   </div>
#   )
# }
# export default App

# sk-131r4qdad421451/welcomeapp/src/HelloWorld.css:
# @import url('https://fonts.googleapis.com/css2?family=Kanit&display=swap');

# .hello-world {
#   display: flex;
#   justify-content: center;
#   align-items: center;
#   height: 100vh;
#   background-color: #f0f2f5;
#   font-family: 'Kanit', sans-serif;
# }

# .hello-world h1 {
#   font-size: 3rem;
#   color: #333;
# }

# .hello-paragraph p {
#     font-size: 1rem;
# }



# ### Find and update the code using the appropriate operations "CREATE" and "UPDATE" that you must incorporate in the existing code:
# UPDATE src/App.tsx
# function App() {
# return (
#   <div>
#     Welcome to AITech
#   </div>
#   )
# }
# export default App;
# ```

# CREATE src/Component.tsx
# ```javascript
# import React from 'react';
# import './HelloWorld.css';

# function HelloWorld() {
#   return (
#     <div className="hello-world">
#       <h1>Hello World!</h1>
#       <p>Welcome to my app!</p>
#     </div>
#   );
# }

# export default HelloWorld;
# ```

# npm install --save-dev css-loader style-loader

# UPDATE src/HelloWorld.css
# ```css
# @import url('https://fonts.googleapis.com/css2?family=Kanit&display=swap');

# .hello-world {
#   display: flex;
#   justify-content: center;
#   align-items: center;
#   height: 100vh;
#   background-color: black;
#   font-family: 'Kanit', sans-serif;
# }

# .hello-world h1 {
#   font-size: 3rem;
#   color: #fff;
# }

# .hello-paragraph p {
#     font-size: 1rem;
# }
# ```
# ### CodeSpinner Response:
# # """           


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

code_snippet =""" function App() {
return (
  <div>
    Welcome to AITech
  </div>
  )
}
export default App"""

WebWriter =f"""
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

prompt = "change the background color to black"
# Example call to the function
# send_completion_request("sk-131r4qdad421451", "8adcadfd-aeb7-4edd-8edd-56efdf5187dd", CodeSpinner, prompt_template)
send_completion_request("sk-131r4qdad421451", "8adcadfd-aeb7-4edd-8edd-56efdf5187dd", WebWriter, prompt)