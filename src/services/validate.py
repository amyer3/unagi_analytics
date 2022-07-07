import json, os

accounts = [

    {
        "username": "lambda",
        "password": "Ow198dfxRVmLVG"
     },
    {
        "username": "izzard",
        "password": "x7pR0uxE4AJO!G0FN&t*b2e!cs^aeuo"
    },
    {
        "username": "lambda_write",
        "password": "ai3Ugdvjztr8SC7t5Z5wJ40u7"
     },
    {
      "username": "iot_backend",
      "password": "18368ec5b614adbd8ff398111a4b648f4062a0e3c4de57eecc7820d584b327e1"
    }
]


def check_auth(username: str, password: str) -> bool:
    if username is None or password is None:
        return False

    for cred in accounts:
        if username == cred['username'] and password == cred['password']:
            return True
    return False