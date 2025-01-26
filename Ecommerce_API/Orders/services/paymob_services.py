import requests
from django.conf import settings
from decouple import config
import hashlib, hmac
import constants
import json

class PaymobServices:
    @classmethod
    def create_intention(cls, amount, currency, biling_data, customer_data, order):
        try:
            headers = {"Authorization": f'Token {config("PAYMOB_SECRET_KEY")}', "Content-Type": 'application/json'}
            data = {
                "amount": int(amount*100),
                "currency": currency,
                "expiration": constants.PAYMENT_EXPIRY,
                "payment_methods": [int(config("PAYMOB_CARD_INTEGRATION_ID"))],
                "billing_data": {
                    "email": biling_data.get('email'),
                    "phone_number": biling_data.get('phone_number'),
                    "first_name": biling_data.get('first_name'),
                    "last_name": biling_data.get('last_name'),
                    "street": biling_data.get('address').get('street'),
                    "building": biling_data.get('address').get('building_no'),
                    "apartment": biling_data.get('address').get('apartment_no'),
                    "country": biling_data.get('address').get('country'),
                },
                "extras": {
                    "store_order_id": order.id
                },
                "customer": {
                    "email": customer_data.email,
                    "first_name": customer_data.name,
                    "last_name": biling_data.get('last_name'),
                },
            }
            intention_data = requests.post(f'{config("PAYMOB_API_BASE_URL")}v1/intention/', json=data, headers=headers)
            intention_data = intention_data.json()
            if 'details' in intention_data:
                raise Exception(intention_data['details'])
            
            order.payment_link = f' https://accept.paymob.com/unifiedcheckout/?publicKey={config('PAYMOB_PUBLIC_KEY')}&clientSecret={intention_data['client_secret']}'
            order.save()
            return {'payment_url': order.payment_link}
        except Exception as e:
            print(e)
            raise Exception('Something went wrong')
    
    
    @classmethod
    def verify_hmac(cls, recieved_hmac, request):
        obj = request.data.get('obj')
        concatenated_data = f"{obj.get('amount_cents')}"\
            f"{obj.get('created_at')}"\
            f"{obj.get('currency')}"\
            f"{"true" if obj.get('error_occured') else "false"}"\
            f"{"true" if obj.get('has_parent_transaction') else "false"}"\
            f"{obj.get('id')}"\
            f"{obj.get('integration_id')}"\
            f"{"true" if obj.get('is_3d_secure') else "false"}"\
            f"{"true" if obj.get('is_auth') else "false"}"\
            f"{"true" if obj.get('is_capture') else "false"}"\
            f"{"true" if obj.get('is_refunded') else "false"}"\
            f"{"true" if obj.get('is_standalone_payment') else "false"}"\
            f"{"true" if obj.get('is_voided') else "false"}"\
            f"{obj.get('order').get('id')}"\
            f"{obj.get('owner')}"\
            f"{"true" if obj.get('pending') else "false"}"\
            f"{obj.get('source_data').get('pan')}"\
            f"{obj.get('source_data').get('sub_type')}"\
            f"{obj.get('source_data').get('type')}"\
            f"{"true" if obj.get('success') else "false"}"
        hashed_data = hmac.new(config('PAYMOB_HMAC_SECRET').encode('utf-8'), concatenated_data.encode('utf-8'), hashlib.sha512).hexdigest()
        return recieved_hmac == hashed_data
    
    
    @classmethod
    def refund_payment(cls, amount, order):
        try:
            headers = {"Authorization": f'Token {config("PAYMOB_SECRET_KEY")}', "Content-Type": 'application/json'}
            data = {
                "amount_cents": int(amount*100),
                "transaction_id": order.paymob_response['obj']['id'],
            }
        ############################################ not working ############################################
            response = requests.post(f'{config("PAYMOB_API_BASE_URL")}api/acceptance/void_refund/refund', json=data, headers=headers)
        except Exception as e:
            print(e)
            raise Exception('Something went wrong')