import os

import bottle
import sendwithus
from bottle import route, request, run

import logging
logging.basicConfig()


@route('/webhook_failed')
def webhook_failed():
    return "ok"


@route('/webhook/contextio', method='POST')
def contextio_webhook():
    try:
        SENDWITHUS_API_KEY = os.environ['SWU_API_KEY']
    except KeyError:
        logging.error("COULD NOT FETCH SENDWITHUS API KEY")
        return 'ok'

    swu = sendwithus.api(SENDWITHUS_API_KEY)

    try:
        data = request.json
    except Exception as e:
        logging.error("Error parsing json: %s\n%s" % (e, request.body))
        return 'ok'

    try:
        email = '%s' % data['message_data']['addresses']['from']['email']
        try:
            # try and fetch customer
            r = swu.customer_details(email)
            if r.status_code == 200:
                customer_data = r.json()['customer']['data']

                # check drip status
                if 'drip_status' in customer_data:
                    if customer_data['drip_status'] == 'active':
                        logging.info('Reply conversion for %s' % email)
                        swu.customer_conversion(email)

                        swu.drip_deactivate(email)

                        customer_data['drip_status'] = 'replied'
                        swu.customer_create(email, data=customer_data)
        except Exception as e:
            # customer probably did not exist
            logging.error("Error with customer %s: %s" % (email, e))
    except Exception as e:
        logging.error("Error with everything: %s\n%s" % (e, request.json))

    return "ok"

if __name__ == "__main__":
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

app = bottle.default_app()
