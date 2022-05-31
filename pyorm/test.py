import base64, zlib
ps_registry = [
    {
        "id": "daily_sales",
        "file": 'daily_sales.sql',
        "connection": "snowflake"
    }

]
def find_prepared_statement(id: str):
    PREPARED_STATEMENT_BASE = './prepareds_scripts/'
    for pid in ps_registry:
        if id == pid['id']:
            query = open(PREPARED_STATEMENT_BASE + pid['file'])
            query = query.read()
            return {"query": query, "connection": pid['connection']}
    return None


if __name__ == '__main__':
    q = find_prepared_statement('daily_sales')
    print(q['query'])
    print(q['connection'])