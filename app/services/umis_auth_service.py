import json
import base64
import requests

def auth_user(data):

    try:
        umisid = data.get('umisid')
        password = data.get('password')

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
        if response.status_code == 200:
            token = response.json()['access_token']

            id = "DICK2010"

            instructor_api = f'https://umis.babcock.edu.ng/babcock/dataserver?view=70:0&linkdata={id}'

            header = {
                'action': 'read',
                'authorization': token
            }

            resp = requests.get(url, headers=header)
            if resp.status_code == 200:
                instructors = resp.json()

                for instructor in instructors['data']:
                    if instructor['instructorid'] == "DICK2010":

                        return instructor, None             
    except Exception as e:
        return None, str(e)