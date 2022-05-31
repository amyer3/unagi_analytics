from flask import Flask, jsonify, request, Response
import json, sys, os, re
from services.find_prepared_statement import *
from services.validate import *
from services.connection_manager import Connection

app = Flask(__name__)
regex_bad_query = re.compile(
    "(delete|truncate|update|drop|insert|create|alter|grant|revoke|commit|save|rollback|rename|merge)", re.IGNORECASE)


@app.route('/write_fx', methods=['POST'])
def write_fx():
    event = request.json
    is_auth = check_auth(event['username'], event['password'])
    if not is_auth or event['username'] != 'lambda_write':
        return jsonify("Invalid Credentials")
    if not event['values'] or event is None:
        return jsonify("no values")
    statement = "insert into fx_rates.rates (quote_date, base_ccy, sale_ccy, created_at, rate) values " + event[
        'values']

    c = Connection()
    event['result'] = c.get_data(connection='snowflake_write', query=statement)
    event['statement'] = statement
    del event['password']
    return jsonify(event)


@app.route("/request", methods=["POST"])
def make_request():
    is_auth = False
    event = request.json
    # if not request.is_secure:
    #     return jsonify("must use https, service will not auto-upgrade for you.")

    if not event['transactions'] or event is None:
        return jsonify("no transactions")

    for cred in accounts:
        if event['username'] == cred['username'] and event['password'] == cred['password']:
            is_auth = True

    if not is_auth or 'username' not in event or event['username'] is None or 'password' not in event or event[
        'password'] is None:
        return jsonify("must provide available username and password in POST body")

    # instantiate connection here
    c = Connection()
    for txn in event['transactions']:
        if 'predefined' in txn:
            q = find_prepared_statement(txn['predefined'])
            txn['query'] = q['query']
            txn['connection'] = q['connection']

        if re.match(regex_bad_query, txn['query']) is not None:
            return jsonify("bad query. you know what you did.")

        tmp = c.get_data(connection=txn['connection'], query=txn['query'])
        txn['result'] = tmp['data']
        txn['columns'] = tmp['columns']
    del event['password']
    return jsonify(event)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
