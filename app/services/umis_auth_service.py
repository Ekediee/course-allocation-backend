import json
import base64
import requests

def auth_user(data):

    try:
        umisid = data.get('umisid')
        password = data.get('password')

        if not umisid or not password:
            return None, "Missing UMIS ID or password"

        username_byte = base64.b64encode(umisid.encode('ascii'))

        username = username_byte.decode('ascii')

        password_byte = base64.b64encode(password.encode('ascii'))

        password = password_byte.decode('ascii')

        header = {
            'Content-Type': 'multipart/form-data',
            'action': 'authorization',
            'authuser': username,
            'authpass': password
        }

        url = 'https://umis.babcock.edu.ng/babcock/dataserver'

        response = requests.post(url, headers=header)

        if response.status_code != 200:
            return None, f"UMIS auth failed ({response.status_code})"
        
        
        token = response.json().get('access_token')
        if not token:
            return None, "No access token received from UMIS"

        # id = "EBIE222"
        # id = "DICK2010"

        instructor_api = f'https://umis.babcock.edu.ng/babcock/dataserver?view=70:0&linkdata={umisid}'

        header = {
            'action': 'read',
            'authorization': token
        }

        resp = requests.get(instructor_api, headers=header)
        if resp.status_code != 200:
            return None, f"Failed to fetch instructor data ({resp.status_code})"
        
        
        instructors = resp.json()
        if 'data' not in instructors or not isinstance(instructors['data'], list):
            return None, "Invalid instructor data format from UMIS"

        for instructor in instructors['data']:
            if instructor.get('instructorid') == umisid:
                return instructor, None
                         
        # If we reach here, no matching instructor was found
        return None, "Instructor not found in UMIS data"
    
    except Exception as e:
        return None, f"UMIS authentication error: {str(e)}"