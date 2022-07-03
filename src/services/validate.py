import sys, json


f = open('keys/user_profiles.json')
accounts = json.load(f)['accounts']


def check_auth(username: str, password: str) -> bool:
    if username is None or password is None:
        return False

    for cred in accounts:
        if username == cred['username'] and password == cred['password']:
            return True
    return False