from .aa_order_data import make_aa_order_data
from .aa_customer_data import make_aa_customer_data
from .dtc_customer_data import make_dtc_customer_data
from .dtc_order_detail import make_dtc_order_detail


def make_main_body(time: str, subs={}, dtc={}, cust={}) -> str:
    body = ''
    if len(subs.keys()) >= 1:
        body += make_aa_customer_data(customer_data=cust) + '</br>' + make_aa_order_data(subs)
    if len(dtc.keys()) >= 1:
        body += make_dtc_customer_data(cust) + '</br>' + make_dtc_order_detail(dtc)
    if body == '':
        # empty body text
        body += '<tr class="center-middle" colspan="10">No data found.</tr>'
    return f"""
    <style>
        .tg {{
            border-collapse: collapse;
            border-spacing: 0;
        }}
    
        .tg td, th {{
            border-color: black;
            border-style: solid;
            border-width: 1px;
            font-family: Monospaced, sans-serif;
            font-size: 12px;
            overflow: hidden;
            padding: 10px 5px;
            word-break: normal;
        }}
    
        .tg .center-middle {{
            text-align: center;
            vertical-align: middle;
        }}
    
        .tg .orange-header {{
            font-weight: bold;
            text-decoration: underline;
            color: #000;
            background-color: #FE996B;
        }}
    
        .tg .black-header {{
            font-weight: bold;
            text-decoration: underline;
            color: #FFF;
            background-color: #000;
        }}
    
        .tg .red-row {{
            font-weight: bold;
            color: black;
            background-color: red;
        }}
    </style>
    <table class="tg">
        <thead>
        <tr>
            <th class="center-middle orange-header" colspan="10">Unagi Customer Information as of: {time}</th>
        </tr>
        </thead>
        {body}
        </tbody>
    </table>
    """

