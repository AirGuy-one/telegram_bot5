import os
import requests
import urllib.request
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv


def get_headers(condition):
    if condition == 'get' or condition == 'remove':
        return {
            'Authorization': f'Bearer {os.environ.get("BEARER")}',
        }
    else:
        return {
            'Authorization': f'Bearer {os.environ.get("BEARER")}',
            'Content-Type': 'application/json'
        }


def get_api_request_json(url):
    return requests.get(url, headers=get_headers('get'))


def post_api_request(url, json):
    return requests.post(url, headers=get_headers('post'), json=json)


def remove_product_request(url):
    requests.delete(url, headers=get_headers('remove'))


def start(update, context):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    response = get_api_request_json(url)
    if response.status_code == 200:
        products = response.json()['data']
    else:
        products = []

    keyboard = [
        [InlineKeyboardButton(product['attributes']['name'],
                              callback_data=str(index)) for index, product in enumerate(products)
         ],
        [InlineKeyboardButton('Cart', callback_data='cart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select a product:",
                             reply_markup=reply_markup)
    return 1


def handle_menu(update, context):
    price_book_id = os.environ.get('PRICE_BOOK_ID')
    url_products = 'https://useast.api.elasticpath.com/pcm/products?include=main_image'
    url_prices = f'https://useast.api.elasticpath.com/pcm/pricebooks/{price_book_id}/prices'
    url_on_stock = 'https://useast.api.elasticpath.com/v2/inventories/multiple'
    products_response = get_api_request_json(url_products)
    prices_response = get_api_request_json(url_prices)

    if products_response.status_code == 200:
        products = products_response.json()['data']
        images = products_response.json()['included']
    else:
        products = []
        images = {}

    if prices_response.status_code == 200:
        prices = prices_response.json()['data']
    else:
        prices = []

    product_index = int(update.callback_query.data)

    product = products[product_index]
    price = str(prices[product_index]['attributes']['currencies']['USD']['amount'])
    on_stock_data = {
        'data': [
            {
                'id': product['id']
            }
        ]
    }
    quantity_on_stock = post_api_request(url_on_stock, on_stock_data).json()['data'][0]['available']

    image_href = images['main_images'][product_index]['link']['href']

    name = product['attributes']['name']
    description = product['attributes']['description']

    message = f"{name}\n\n{price[:-2]}.{price[-2:]} per kg\n{quantity_on_stock}kg on stock\n\n{description}"

    urllib.request.urlretrieve(
        image_href,
        'image.png'
    )

    keyboard = [
        [
            InlineKeyboardButton('1 kg', callback_data=f"1::{product['id']}"),
            InlineKeyboardButton('5 kg', callback_data=f"5::{product['id']}"),
            InlineKeyboardButton('10 kg', callback_data=f"10::{product['id']}")
        ],
        [InlineKeyboardButton('Cart', callback_data='cart')],
        [InlineKeyboardButton('Back to the menu', callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open('image.png', 'rb'),
        reply_markup=reply_markup,
        caption=message
    )


def handle_back(update, context):
    return start(update, context)


def handle_add_product_to_cart(update, context):
    cart_id = os.environ.get('CART_ID')
    url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items"
    data = {
        "data": {
            "id": update.callback_query.data.split('::')[1],
            "type": "cart_item",
            "quantity": int(update.callback_query.data.split('::')[0]),
        }
    }
    post_api_request(url, data)


def handle_cart(update, context):
    cart_id = os.environ.get('CART_ID')
    url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items"

    response = get_api_request_json(url)

    if response.status_code == 200:
        cart_items = response.json()['data']
    else:
        cart_items = []

    message = ''
    for cart_item in cart_items:
        price = cart_item['meta']['display_price']['without_tax']['unit']
        amount = cart_item['meta']['display_price']['without_tax']['value']
        kg_quantity = int(amount['amount'] / price['amount'])
        message += f"{cart_item['name']}\n" \
                   f"{cart_item['description']}\n" \
                   f"{price['formatted']} per kg\n" \
                   f"{kg_quantity}kg in cart for {amount['formatted']}\n\n"

    message += f"Total: {response.json()['meta']['display_price']['without_tax']['formatted']}"

    keyboard = [
        [InlineKeyboardButton(f'Remove from the cart the {cart_item["name"]}',
                              callback_data=f'rm::{cart_item["id"]}')] for cart_item in cart_items]
    keyboard.append([InlineKeyboardButton('Back to the menu', callback_data='back')])
    keyboard.append([InlineKeyboardButton('Pay for it', callback_data='pay')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup
    )


def handle_remove_product_from_cart(update, context):
    cart_id = os.environ.get('CART_ID')
    cart_item_id = update.callback_query.data.split("::")[1]
    url = f'https://useast.api.elasticpath.com/v2/carts/{cart_id}/items/{cart_item_id}'
    remove_product_request(url)
    handle_cart(update, context)


def handle_payment(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your email address:")


def payment_message(update, context):
    url = 'https://useast.api.elasticpath.com/v2/customers'
    user_email = update.message.text
    data = {
        'data':
            {
                "type": "customer",
                "name": "First user",
                "email": user_email
            }
    }

    post_api_request(url, data)

    message = f"Your email is: {user_email}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    return 1


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_back, pattern='back'))
    dispatcher.add_handler(CallbackQueryHandler(handle_cart, pattern='cart'))
    dispatcher.add_handler(CallbackQueryHandler(handle_payment, pattern='pay'))
    dispatcher.add_handler(CallbackQueryHandler(handle_add_product_to_cart, pattern=r"^\d*::.*$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_remove_product_from_cart, pattern=r"^rm::.+$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    dispatcher.add_handler(MessageHandler(Filters.text, payment_message))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
