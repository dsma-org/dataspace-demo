import jwt, time, requests, json, urllib.parse

def extract_exp_and_sub(decoded_token):
    exp = decoded_token.get('exp')
    sub = decoded_token.get('sub')
    return exp, sub

def is_token_expired(exp):
    current_time = int(time.time())
    return exp < current_time

def decode_jwt_from_json(access_token):
    if not access_token:
        return {'error': 'Access token not found in JSON data.'}
    
    try:
        decoded_token = jwt.decode(access_token, algorithms=['HS256'], options={"verify_signature": False})
        return decoded_token
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired.'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token.'}

def get_token_from_json(json_data):
    json_data = json.loads(json_data)
    access_token = json_data.get('access_token')
    refresh_token = json_data.get('refresh_token')
    return access_token, refresh_token


def unixAddTime():
    current_time = int(time.time())
    addTimeSecs = 172800
    return current_time + addTimeSecs

def is_valid_user(username, password):
    return username == "example_user" and password == "example_password"

def get_auth_data(code, username, password):
    if is_valid_user(username, password):
        access_token, refresh_token, sub, exp = "", "", 0, unixAddTime()

    else:
        json_data = get_token_auth_code(code, username, password)
        access_token, refresh_token = get_token_from_json(json_data)
        decoded_token = decode_jwt_from_json(access_token)

        exp, sub = extract_exp_and_sub(decoded_token)
        if exp:
            if is_token_expired(exp):
                print("Token has expired, getting refresh token")
                access_token, refresh_token = refresh_access_token(refresh_token)
                decoded_token = decode_jwt_from_json(access_token)
                exp, sub = extract_exp_and_sub(decoded_token)
                if is_token_expired(exp):
                    print("Please login to the IoP-Portal")
                    access_token = None
                    refresh_token = None
                    sub = None
                    exp = None
                else:
                    print("Token is valid.")
            else:
                print("Token is still valid.")
        else:
            print("Expiration time not found in token.")

    return access_token, refresh_token, sub, exp

def api_call(headers, payload):
    url = "https://example.com//o/oauth2/token"
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text

def get_token_auth_code(code, username, password):
    if username and password:
        payload = f'grant_type=password&client_id=id-....&client_secret=secret....&username={urllib.parse.quote(username)}&password={urllib.parse.quote(password)}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'COOKIE_SUPPORT=true; GUEST_LANGUAGE_ID=en_US'
        }
    elif code:
        payload = f'grant_type=authorization_code&client_id=id-....&client_secret=secret-....&code={code}'
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'COOKIE_SUPPORT=true; GUEST_LANGUAGE_ID=en_US; JSESSIONID=....'
        }
    return api_call(headers, payload)

def refresh_access_token(refresh_token):
    payload = f'grant_type=refresh_token&client_id=id....&client_secret=secret-....&refresh_token={refresh_token}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    new_token = api_call(headers, payload)
    return get_token_from_json(new_token)
