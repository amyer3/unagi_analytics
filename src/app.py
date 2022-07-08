from flask import Flask, jsonify, request
from threading import Thread
from services.find_prepared_statement import *
from services.validate import check_auth
from services.connection_manager import Connection
from services.query_security import check_bad_ddl
from webhooks.zendesk_new_ticket.WEBHOOK_zendesk_new_ticket import search_and_update

app = Flask(__name__)
c = Connection()

@app.route('/hb', methods=['GET'])
def heartbeat():
    return jsonify(success=True)


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

    event['result'] = c.get_data(connection='snowflake_write', query=statement)
    event['statement'] = statement
    del event['password']
    return jsonify(event)


@app.route("/webhook/<string:service>/<string:action>", methods=["POST", "GET"])
def execute_webhook(service: str, action: str):
    event = request.json
    print(event)
    if service == 'zendesk':
        if action == 'new_ticket':
            Thread(
                target=search_and_update(ticket_id=event['ticket']['id'], connection=c, email=event['ticket']['email'],
                                         phone=event['ticket']['phone'])).start()
    return jsonify(success=True)


@app.route("/docs", methods=["GET"])
def serve_docs():
    pass

#TODO: add in prepared statement to select & return full row from sub_current_status postgres
@app.route("/request", methods=["POST"])
def make_request():
    event = request.json
    is_auth = check_auth(event['username'], event['password'])
    if not request.is_secure:
        return jsonify("must use https, service will not auto-upgrade for you.")

    if not event['transactions'] or event is None:
        return jsonify("no transactions")

    if not is_auth or 'username' not in event or event['username'] is None or 'password' not in event or event[
        'password'] is None:
        return jsonify("must provide available username and password in POST body")

    for txn in event['transactions']:
        if 'predefined' in txn:
            append = txn['fields'] if 'fields' in txn.keys() else {}
            q = find_prepared_statement(txn['predefined'], append)
            txn['query'] = q['query']
            txn['connection'] = q['connection']

        if check_bad_ddl(txn['query']) is not None:
            return jsonify("bad query. you know what you did.")

        tmp = c.get_data(connection=txn['connection'], query=txn['query'])
        if 'data' in tmp.keys():
            txn['result'] = tmp['data']
        if 'columns' in tmp.keys():
            txn['columns'] = tmp['columns']
        if 'data' not in tmp.keys() or len(tmp['data']) == 0:
            txn['result'] = []
            txn['message'] = 'no data found'
    del event['password']
    return jsonify(event)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
