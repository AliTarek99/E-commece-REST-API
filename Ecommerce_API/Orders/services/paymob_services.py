import requests
from django.conf import settings
from decouple import config

class PaymobServices:
    @classmethod
    def create_intention(cls, amount, currency, items, biling_data, customer_data):
        headers = {'Authorization': f'Token {config("PAYMOB_SECRET_KEY")}', 'Content-Type': 'application/json'}
        data = {
            'amount': amount,
            'currency': currency,
            'payment_methods': [config("PAYMOB_CARD_INTEGRATION_ID")],
            'billing_data': {
                'email': biling_data.get('email'),
                'phone_number': biling_data.get('phone_number'),
                'first_name': biling_data.get('first_name'),
                'last_name': biling_data.get('last_name'),
                'street': biling_data.get('street'),
                'building': biling_data['building'],
                'floor': biling_data.get('floor'),
                'apartment': biling_data.get('apartment'),
                'country': biling_data.get('country'),
                'state': biling_data.get('state'),
            },
            'customer': {
                'email': customer_data.get('email'),
                'first_name': customer_data.get('first_name'),
                'last_name': customer_data.get('last_name'),
            },
            items: items
        }
        intention_data = requests.post(f'{config("PAYMOB_BASE_URL")}/intention/', data=data, headers=headers)
        intention_data = intention_data.json()
        if 'details' in intention_data:
            raise Exception(intention_data['details'])
        return {'payment_url': f' https://accept.paymob.com/unifiedcheckout/?publicKey={config('PAYMOB_PUBLIC_KEY')}&clientSecret={intention_data['client_secret']}'}