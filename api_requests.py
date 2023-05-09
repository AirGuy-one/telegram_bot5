import requests
import os


def get_products(bearer):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {bearer}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_products_with_images(bearer):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {bearer}',
    }
    params = {
        'include': 'main_image'
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    json_response = response.json()
    return json_response['data'], json_response['included']


def get_prices(bearer):
    price_book_id = os.environ.get('PRICE_BOOK_ID')
    url = f'https://useast.api.elasticpath.com/pcm/pricebooks/{price_book_id}/prices'
    headers = {
        'Authorization': f'Bearer {bearer}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_quantity_on_stock(product_id, bearer):
    url = 'https://useast.api.elasticpath.com/v2/inventories/multiple'
    headers = {
        'Authorization': f'Bearer {bearer}',
        'Content-Type': 'application/json'
    }
    data = {
        'data': [
            {
                'id': product_id
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['data'].pop()['available']


def get_cart_items_and_total_sum(bearer):
    cart_id = os.environ.get('CART_ID')
    url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items"
    headers = {
        'Authorization': f'Bearer {bearer}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    json_response = response.json()
    return json_response['data'], json_response['meta']['display_price']['without_tax']['formatted']


def create_cart(user_id, bearer):
    url = "https://useast.api.elasticpath.com/v2/carts"
    headers = {
        'Authorization': f'Bearer {bearer}',
        'Content-Type': 'application/json'
    }
    json = {
        "data": {
            "name": f"Cart of user with {user_id} id",
            "description": "For Holidays",
            "discount_settings": {
                "custom_discounts_enabled": True
            }
        }
    }
    response = requests.post(url, headers=headers, json=json)
    response.raise_for_status()
    return response.json()['data']['id'].decode('utf-8')


def add_product_to_cart(cart_id, quantity, product_id, bearer):
    url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items"
    headers = {
        'Authorization': f'Bearer {bearer}',
        'Content-Type': 'application/json'
    }
    data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": int(quantity),
        }
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def push_customer_data(user_email, bearer):
    url = 'https://useast.api.elasticpath.com/v2/customers'
    headers = {
            'Authorization': f'Bearer {bearer}',
            'Content-Type': 'application/json'
    }
    json = {
        'data':
            {
                "type": "customer",
                "name": "First user",
                "email": user_email
            }
    }
    response = requests.post(url, headers=headers, json=json)
    response.raise_for_status()


def remove_product(cart_id, cart_item_id, bearer):
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items/{cart_item_id}'
    headers = {
        'Authorization': f'Bearer {bearer}',
    }
    requests.delete(url, headers=headers)