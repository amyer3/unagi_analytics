import json, os

accounts = [

    {
        "username": "lambda",
        "password": "Ow198dfxRVmLVG",
        "permission": 'read'
    },
    {
        "username": "izzard",
        "password": "x7pR0uxE4AJO!G0FN&t*b2e!cs^aeuo",
        "permission": 'read'
    },
    {
        "username": "lambda_write",
        "password": "ai3Ugdvjztr8SC7t5Z5wJ40u7",
        "permission": 'write'
    },
    {
        "username": "iot_backend",
        "password": "18368ec5b614adbd8ff398111a4b648f4062a0e3c4de57eecc7820d584b327e1",
        "permission": 'read'
    }
]


def check_auth(username: str, password: str) -> (bool, [str]):
    if username is None or password is None:
        return (False, None)

    for cred in accounts:
        if username == cred['username'] and password == cred['password']:
            return (True, cred['permission'])
    return (False, None)
