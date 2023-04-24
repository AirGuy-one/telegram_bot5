import os
import logging
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv

START, ECHO = range(2)


def start(update, context):
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select an option:",
                             reply_markup=reply_markup)
    return ECHO


def echo(update, context):
    if update.message.text == '/start':
        return start(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    return ECHO


def handle_users_reply(update, context):
    db = redis.Redis(
        host=os.environ.get('DATABASE_HOST'),
        port=int(os.environ.get('DATABASE_PORT')),
        db=0,
        password=os.environ.get('DATABASE_PASSWORD'),
    )
    chat_id = str(update.effective_chat.id)
    state = db.get(chat_id)
    if state is None:
        state = START
    else:
        state = int(state)

    db.set(chat_id, state)


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
