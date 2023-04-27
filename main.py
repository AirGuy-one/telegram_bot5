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
         ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select an option:",
                             reply_markup=reply_markup)
    return ECHO


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    return ECHO


def handle_users_reply(update, context):
    url_products = 'https://useast.api.elasticpath.com/pcm/products?include=main_image'
    price_book_id = os.environ.get('PRICE_BOOK_ID')
    url_prices = f'https://useast.api.elasticpath.com/pcm/pricebooks/{price_book_id}/prices'
    headers = {
        'Authorization': f'Bearer {os.environ.get("BEARER")}'
    }
    response = requests.get(url_products, headers=headers).json()

    products = response['data']
    prices = requests.get(url_prices, headers=headers).json()['data']
    images = response['included']

    product_index = int(update.callback_query.data)

    product = products[product_index]
    price = str(prices[product_index]['attributes']['currencies']['USD']['amount'])

    image_href = images['main_images'][product_index]['link']['href']

    name = product['attributes']['name']
    description = product['attributes']['description']

    message = f"{name}\n\n{price[:-2]}.{price[-2:]} per kg\n\n{description}"

    urllib.request.urlretrieve(
        image_href,
        'image.png'
    )

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open('image.png', 'rb'),
        caption=message
    )


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
