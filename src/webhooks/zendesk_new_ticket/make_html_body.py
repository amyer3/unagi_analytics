from templates.container import make_main_body


def make_html(time, sub_data, dtc_data, customer_data):
    html = make_main_body(time=time, subs=sub_data, dtc=dtc_data, cust=customer_data)
    # formatting to make sure zendesk can read this
    # currently, can not do \n new lines or unescaped " (via JSON)

    # we want all table cells to be center aligned, but Zendesk rendering doesn't support
    # vertical align tag. Just deal with it, CS
    html = html.replace('<td', '<td class="center" style="vertical-align: middle;" ')
    html = html.replace('\n', '')

    # make sure that " characters appear in the JSON correctly, not needed for requests pkg
    #html = html.replace('"', '\"')
    return html

