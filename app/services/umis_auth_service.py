import json
import base64
import requests
import os
from dotenv import load_dotenv
from flask import session

# Load the variables from .env
load_dotenv()
    
def auth_user(data):
    """
    Authenticates with UMIS and fetches instructor data.
    Reuses the UMIS token from the Flask session if available.
    """
    try:
        umisid = data.get('umisid')
        password = data.get('password')

        if not umisid or not password:
            return None, "Missing UMIS ID or password"
        
        # For development/testing purposes
        temp_dept = ''

        if "computer" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0] # This ID is development only

        if "mass_com" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0]

        if "software" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0]

        if "religious" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0]

        if "nutrition" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0]

        if "anatomy" in umisid:
            temp_dept = umisid.split("-")[1]
            umisid = umisid.split("-")[0]

        # Check for an existing token first
        umis_token = session.get('umis_token')

        if not umis_token:
            # If no token in session, perform the full authentication
            # print("No UMIS token in session. Fetching a new one.") # Good for debugging
            
            username_byte = base64.b64encode(umisid.encode('ascii'))
            username = username_byte.decode('ascii')
            password_byte = base64.b64encode(password.encode('ascii'))
            password_enc = password_byte.decode('ascii')

            header = {
                'Content-Type': 'multipart/form-data',
                'action': 'authorization',
                'authuser': username,
                'authpass': password_enc
            }
            url = os.getenv('UMIS_AUTH_URL')
            response = requests.post(url, headers=header)

            if response.status_code != 200:
                return None, f"UMIS auth failed ({response.status_code})"
            
            token_data = response.json()
            umis_token = token_data.get('access_token')
            if not umis_token:
                return None, "No access token received from UMIS"

            # STORE THE NEW TOKEN IN THE SESSION
            session['umis_token'] = umis_token

        # For development/testing purposes
        if "computer" in temp_dept:
            umisid = "EBIE222"

        if "software" in temp_dept:
            umisid = "MAI2010"

        if "mass_com" in temp_dept:
            umisid = "ATAK111"

        if "religious" in temp_dept:
            umisid = "DICK2010"

        if "nutrition" in temp_dept:
            umisid = "ANI101"

        if "anatomy" in temp_dept:
            umisid = "ADEL444"

        # FETCH INSTRUCTOR DATA
        instructor_api = f"{os.getenv('UMIS_INSTRUCTOR_URL')}{umisid}"
        header = {
            'action': 'read',
            'authorization': umis_token
        }
        resp = requests.get(instructor_api, headers=header)

        # --- ADVANCED: Handle expired tokens ---
        # if resp.status_code == 401:
        #     print("UMIS token expired. Clearing from session and retrying.")
        #     session.pop('umis_token', None) # Remove the bad token
        #     # We can recursively call the function again to get a new token.
        #     # This is a robust way to handle expiration.
        #     return auth_user(data)

        if resp.status_code != 200:
            return None, f"Failed to fetch instructor data ({resp.status_code})"
        
        instructors = resp.json()
        if 'data' not in instructors or not isinstance(instructors['data'], list):
            return None, "Invalid instructor data format from UMIS"

        for instructor in instructors['data']:
            if instructor.get('instructorid') == umisid:
                return instructor, None, umis_token, umisid # Success
                         
        return None, "Instructor not found in UMIS data"
    
    except Exception as e:
        return None, f"UMIS authentication error: {str(e)}"
    

def auth_dev_user():
    """
    Authenticates with UMIS and push allocation.
    """
    try:
        umisid = os.getenv('API_DEV_ID')
        password = os.getenv('API_DEV_PASSWORD')

        if not umisid or not password:
            return None, "Missing UMIS ID or password"
        
            
        username_byte = base64.b64encode(umisid.encode('ascii'))
        username = username_byte.decode('ascii')
        password_byte = base64.b64encode(password.encode('ascii'))
        password_enc = password_byte.decode('ascii')

        header = {
            'Content-Type': 'multipart/form-data',
            'action': 'authorization',
            'authuser': username,
            'authpass': password_enc
        }
        url = os.getenv('UMIS_AUTH_URL')
        response = requests.post(url, headers=header)

        if response.status_code != 200:
            return None, f"UMIS auth failed ({response.status_code})"
        
        token_data = response.json()
        umis_token = token_data.get('access_token')
        if not umis_token:
            return None, "No access token received from UMIS"
                         
        return umis_token, None # Success
    
    except Exception as e:
        return None, f"UMIS authentication error: {str(e)}"