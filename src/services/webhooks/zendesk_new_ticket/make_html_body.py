from .templates.container import make_main_body

def make_html(time, sub_data, dtc_data, customer_data):
    html = make_main_body(time=time, subs=sub_data, dtc=dtc_data, cust=customer_data)
    # formatting to make sure zendesk can read this
    # currently, can not do \n new lines or unescaped " (via JSON)
    html = html.replace('\n', '')
    html = html.replace('"', '\"')
    return html

