import re


blocked_keywords = {
    'read': re.compile(
    "(delete|truncate|update|drop|insert|create|alter|grant|revoke|commit|save|rollback|rename|merge)", re.IGNORECASE),
    'write': re.compile('')
}
# check for perenthesis, commas, and no DML / DDL language or comments
insert_values = ''

def includes_blocked_keywords(query: str, permission: str) -> any:
    if re.match(blocked_keywords[permission], query) is not None:
        return True
    return False
