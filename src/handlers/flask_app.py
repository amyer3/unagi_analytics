from flask import Flask, jsonify, request
import json, sys, os, psycopg2
import snowflake.connector as snowflake_connector

schema = {
    "transactions": [
        {
            "connection": "postgres",
            "method": "get",
            "query": "SELECT * FROM slot",
            "columns": "todo"
        },
        {
            "connection": "snowflake",
            "method": "get",
            "query": "SELECT * FROM FIVETRAN_STRIPE.SUBSCRIPTION"
        }
    ]

}


class Connection:
    def __init__(self):
        self.cursors = {
            "postgres": self.pg_connect(),
            "snowflake": self.sf_connect()
        }
        self.query_history = []

    def route_method(self, method: str):
        pass

    def check_connection(self, connection: str):
        if connection not in self.cursors:
            raise Exception("Unknown connection identifier: %s passed to Connection.get_data(), options are: %s" % (
                connection, ', '.join(self.cursors.keys())))
        return

    def update_data(self, connection: str, query: str):
        self.check_connection(connection=connection)

    def get_data(self, connection: str, query: str):
        self.check_connection(connection=connection)

        c = self.cursors[connection]
        try:
            c.execute(query)
            results = c.fetchall()
            return results
        except Exception:
            pass

    def pg_connect(self):
        try:
            return psycopg2.connect(
                host="db-postgresql-sfo2-76942-do-user-8637590-0.b.db.ondigitalocean.com",
                dbname="defaultdb-pool",
                user="doadmin",
                password="kiutqfyoi3kiz1ce",
                port='25061',
                sslmode='require'
            ).cursor()
        except Exception:
            pass

    def sf_connect(self):
        try:
            return snowflake_connector.connect(
                user='RETOOL_USER',
                password='O9am8Aj(1ma*',
                account='mk25046.us-central1.gcp',
                warehouse='SEGMENT_WAREHOUSE',
                database='UNAGI_EDW'
            ).cursor()
        except Exception:
            pass


app= Flask(__name__)

@app.route("/request", methods=["POST"])
def make_request():
    event = request.json
    if not event['transactions'] or event is None:
        return jsonify("no transactions")
    c = Connection()
    for txn in event['transactions']:
        txn['result'] = c.get_data(connection=txn['connection'], query=txn['query'])

    return event

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')