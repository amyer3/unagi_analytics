import re

regex_bad_query = re.compile(
    "(delete|truncate|update|drop|insert|create|alter|grant|revoke|commit|save|rollback|rename|merge)", re.IGNORECASE)

# check for perenthesis, commas, and no DML / DDL language or comments
insert_values = ''

def check_bad_ddl(query: str) -> any:
    if re.match(regex_bad_query, query) is not None:
        return "bad query. you know what you did."
