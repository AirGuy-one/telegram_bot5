import os
import logging
import redis
import requests
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
        [InlineKeyboardButton(product['attributes']['name'], callback_data='1') for product in products]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select an option:",
                             reply_markup=reply_markup)
    return ECHO


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    return ECHO


# def handle_users_reply(update, context):
#     if update.message.text == ''


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
