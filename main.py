import os
import urllib.request
import urllib.error
import redis
import textwrap

from token_update import get_access_token
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv
from api_requests import get_products, get_products_with_images, get_prices, get_product_quantity_on_stock, \
    get_cart_items_and_total_sum, create_cart, add_product_to_cart, push_customer_data, remove_product


def change_token(context):
    context.bot_data['access_token'] = get_access_token()
    context.bot.send_message(context.job.context, text=f"{context.bot_data['access_token']} token has changed!")


def start(update, context):
    keyboard = [
        [InlineKeyboardButton(product['attributes']['name'],
                              callback_data=str(index)) for index, product in
         enumerate(get_products(context.bot_data['access_token']))
         ],
        [InlineKeyboardButton('Cart', callback_data='cart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please select a product:",
                             reply_markup=reply_markup)

    if hasattr(update.message, 'chat_id'):
        context.job_queue.run_repeating(change_token, 60 * 60, context=update.message.chat_id)


def handle_menu(update, context):
    products, images = get_products_with_images(context.bot_data['access_token'])
    prices = get_prices(context.bot_data['access_token'])

    product_index = int(update.callback_query.data)

    product = products[product_index]
    price = str(prices[product_index]['attributes']['currencies']['USD']['amount'])

    quantity_on_stock = get_product_quantity_on_stock(product['id'], context.bot_data['access_token'])

    image_href = images['main_images'][product_index]['link']['href']

    name = product['attributes']['name']
    description = product['attributes']['description']

    message = f"{name}\n\n{price[:-2]}.{price[-2:]} per kg\n{quantity_on_stock}kg on stock\n\n{description}"

    try:
        urllib.request.urlretrieve(image_href, 'image.png')
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}")

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

    with open('image.png', 'rb') as f:
        photo = f.read()

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo,
        reply_markup=reply_markup,
        caption=message
    )


def handle_back(update, context):
    return start(update, context)


def handle_add_product_to_cart(update, context):
    r = context.bot_data['r']

    user_id = update.effective_user.id

    # Binding telegram_id to the cart_id in redis
    if r.exists(f"cart:{user_id}"):
        cart_id = r.get(f"cart:{user_id}").decode('utf-8')
    else:
        cart_id = create_cart(user_id, context.bot_data['access_token'])
        r.set(f"cart:{user_id}", cart_id)

    context.bot_data['cart_id'] = cart_id

    quantity, product_id = update.callback_query.data.split('::')
    add_product_to_cart(cart_id, quantity, product_id, context.bot_data['access_token'])


def handle_cart(update, context):
    cart_items, total = get_cart_items_and_total_sum(context.bot_data['access_token'])

    message = ''
    for cart_item in cart_items:
        price = cart_item['meta']['display_price']['without_tax']['unit']
        amount = cart_item['meta']['display_price']['without_tax']['value']
        kg_quantity = int(amount['amount'] / price['amount'])
        message += textwrap.dedent(f"""
            {cart_item['name']}
            {cart_item['description']}
            {price['formatted']} per kg
            {kg_quantity}kg in cart for {amount['formatted']}

        """)

    message += f"Total: {total}"

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
    cart_id = context.bot_data['cart_id']
    rm_indicator, cart_item_id = update.callback_query.data.split("::")
    remove_product(cart_id, cart_item_id, context.bot_data['access_token'])
    handle_cart(update, context)


def handle_payment(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your email address:")


def payment_message(update, context):
    user_email = update.message.text
    push_customer_data(user_email, context.bot_data['access_token'])

    message = f"Your email is: {user_email}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def main():
    load_dotenv()

    r = redis.Redis(
        host=os.environ.get('DATABASE_HOST'),
        port=int(os.environ.get('DATABASE_PORT')),
        password=os.environ.get('DATABASE_PASSWORD'),
        db=0
    )

    initial_token = os.environ.get("TELEGRAM_TOKEN")
    updater = Updater(initial_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['r'] = r

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_back, pattern='back'))
    dispatcher.add_handler(CallbackQueryHandler(handle_cart, pattern='cart'))
    dispatcher.add_handler(CallbackQueryHandler(handle_payment, pattern='pay'))
    dispatcher.add_handler(CallbackQueryHandler(handle_add_product_to_cart, pattern=r"^\d*::.*$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_remove_product_from_cart, pattern=r"^rm::.+$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    dispatcher.add_handler(MessageHandler(Filters.text, payment_message))

    dispatcher.bot_data['access_token'] = get_access_token()

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
