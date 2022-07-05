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
     }
]


def check_auth(username: str, password: str) -> bool:
    if username is None or password is None:
        return False

    for cred in accounts:
        if username == cred['username'] and password == cred['password']:
            return True
    return False