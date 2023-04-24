import os
import logging
import redis
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv

START, ECHO = range(2)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет!")
    return ECHO


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    return ECHO


states = {
    START: [CommandHandler('start', start)],
    ECHO: [MessageHandler(Filters.text, echo)]
}


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

    handlers = states[state]
    new_state = None
    for handler in handlers:
        new_state = handler.callback(update, context)
        if new_state is not None:
            state = new_state
    db.set(chat_id, state)


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))

    updater.start_polling()


if __name__ == '__main__':
    load_dotenv()
    main()
