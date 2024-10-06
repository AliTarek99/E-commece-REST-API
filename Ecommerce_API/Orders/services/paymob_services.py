import requests
from django.conf import settings
from decouple import config
import hashlib, hmac

class PaymobServices:
    @classmethod
    def create_intention(cls, amount, currency, items, biling_data, customer_data, order_id):
        try:
            print('0'*500)
            headers = {'Authorization': f'Token {config("PAYMOB_SECRET_KEY")}', 'Content-Type': 'application/json'}
            data = {
                'merchant_order_id': order_id,
                'amount': amount*100,
                'currency': currency,
                'expiration': 5800,
                'payment_methods': [config("PAYMOB_CARD_INTEGRATION_ID")],
                'billing_data': {
                    'email': biling_data.get('email'),
                    'phone_number': biling_data.get('phone_number'),
                    'first_name': biling_data.get('first_name'),
                    'last_name': biling_data.get('last_name'),
                    'street': biling_data.get('street'),
                    'building': biling_data.get('building'),
                    'floor': biling_data.get('floor'),
                    'apartment': biling_data.get('apartment'),
                    'country': biling_data.get('country'),
                    'state': biling_data.get('state'),
                },
                'customer': {
                    'email': customer_data.email,
                    'first_name': customer_data.name,
                    'last_name': biling_data.get('last_name')
                },
                'items': [{"name": item.name, "amount": item.price*100, "description": item.description, "quantity": item.quantity} for item in items]
            }
            intention_data = requests.post(f'{config("PAYMOB_API_BASE_URL")}/v1/intention/', data=data, headers=headers)
            print('2'*500, intention_data.content)
            intention_data = intention_data.json()
            if 'details' in intention_data:
                raise Exception(intention_data['details'])
            return {'payment_url': f' https://accept.paymob.com/unifiedcheckout/?publicKey={config('PAYMOB_PUBLIC_KEY')}&clientSecret={intention_data['client_secret']}'}
        except Exception as e:
            print(e)
            raise Exception('Something went wrong')
    
    @classmethod
    def verify_hmac(cls, hmac, request):
        obj = request.data.get('obj')
        concatenated_data = f"""{obj.get('amount_cents')}
            {obj.get('created_at')}
            {obj.get('currency')}
            {obj.get('error_occured')}
            {obj.get('has_parent_transaction')}
            {obj.get('id')}
            {obj.get('integration_id')}
            {obj.get('is_3d_secure')}
            {obj.get('is_auth')}
            {obj.get('is_capture')}
            {obj.get('is_refunded')}
            {obj.get('is_standalone_payment')}
            {obj.get('is_voided')}
            {obj.get('order').get('id')}
            {obj.get('owner')}
            {obj.get('pending')}
            {obj.get('source_data').get('pan')}
            {obj.get('source_data').get('sub_type')}
            {obj.get('source_data').get('type')}
            {obj.get('success')}"""
            
        hashed_data = hmac.new(config('PAYMOB_HMAC_SECRET'), concatenated_data.encode('utf-8'), hashlib.sha512).hexdigest()
        
        return hmac == hashed_data