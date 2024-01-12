import json

import requests

from constants import BASE_URL, HEADERS


def _make_request(method, endpoint, data=None, params=None, headers=None):
    url = f"{BASE_URL}{endpoint}"
    response = requests.request(
        method,
        url,
        headers=headers,
        json=data,
        params=params
    )
    return response


def _print_response(response):
    print()
    print(f"Response Code: {response.status_code}")
    try:
        response_data = response.json()
        print("Response JSON:")
        print(json.dumps(response_data, indent=2))
    except ValueError:
        print("Response Content:")
        print(response.text)


def login_user():
    data = {
        "email": "root@root.com",
        "password": "root"
    }
    response = _make_request('POST', endpoint="/auth/login", data=data, headers=HEADERS)

    return json.loads(response.text)


def get_user(username):
    headers = login_user()
    headers= {"Authorization":f"Bearer {headers['token']}"}
    response = _make_request('GET', endpoint="/user", params={"string": username}, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def delete_user(id):
    headers = login_user()
    headers = {"Authorization": f"Bearer {headers['token']}"}

    response = _make_request('delete', endpoint="/admin/user", params={"id":id}, headers=headers)

    if response.status_code == 200:
        return True
    else:
        return False
