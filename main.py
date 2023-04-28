import os
import requests
import urllib.request

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv

START, ECHO = range(2)


def start(update, context):
    url = 'https://useast.api.elasticpath.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {os.environ.get("BEARER")}'
    }
    products = requests.get(url, headers=headers).json()['data']

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
    return ECHO


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    return ECHO


def handle_menu(update, context):
    price_book_id = os.environ.get('PRICE_BOOK_ID')
    url_products = 'https://useast.api.elasticpath.com/pcm/products?include=main_image'
    url_prices = f'https://useast.api.elasticpath.com/pcm/pricebooks/{price_book_id}/prices'
    url_on_stock = 'https://useast.api.elasticpath.com/v2/inventories/multiple'
    headers = {
        'Authorization': f'Bearer {os.environ.get("BEARER")}',
        'Content-Type': 'application/json'
    }
    products_response = requests.get(url_products, headers=headers).json()

    products = products_response['data']
    prices = requests.get(url_prices, headers=headers).json()['data']
    images = products_response['included']

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
    quantity_on_stock = requests.post(url_on_stock, headers=headers, json=on_stock_data).json()['data'][0]['available']

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
    headers = {
        'Authorization': f'Bearer {os.environ.get("BEARER")}',
        'Content-Type': 'application/json'
    }
    data = {
        "data": {
            "id": update.callback_query.data.split('::')[1],
            "type": "cart_item",
            "quantity": int(update.callback_query.data.split('::')[0]),
        }
    }
    requests.post(url, headers=headers, json=data)


def handle_cart(update, context):
    cart_id = os.environ.get('CART_ID')
    url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items"

    headers = {
        "Authorization": f"Bearer {os.environ.get('BEARER')}",
    }

    response = requests.get(url, headers=headers).json()

    cart_items = response['data']
    message = ''
    for cart_item in cart_items:
        price = cart_item['meta']['display_price']['without_tax']['unit']
        amount = cart_item['meta']['display_price']['without_tax']['value']
        kg_quantity = int(amount['amount'] / price['amount'])
        message += f"{cart_item['name']}\n" \
                   f"{cart_item['description']}\n" \
                   f"{price['formatted']} per kg\n" \
                   f"{kg_quantity}kg in cart for {amount['formatted']}\n\n"

    message += f"Total: {response['meta']['display_price']['without_tax']['formatted']}"

    keyboard = [
        [InlineKeyboardButton(f'Remove from the cart the {cart_item["name"]}',
                              callback_data=f'rm::{cart_item["id"]}')] for cart_item in cart_items
    ]
    keyboard.append([InlineKeyboardButton('Back to the menu', callback_data='back')])

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
    headers = {
        'Authorization': f'Bearer {os.environ.get("BEARER")}',
    }
    requests.delete(url, headers=headers)
    handle_cart(update, context)


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_back, pattern='back'))
    dispatcher.add_handler(CallbackQueryHandler(handle_cart, pattern='cart'))
    dispatcher.add_handler(CallbackQueryHandler(handle_add_product_to_cart, pattern=r"^\d*::.*$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_remove_product_from_cart, pattern=r"^rm::.+$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
