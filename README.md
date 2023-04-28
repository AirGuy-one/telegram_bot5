# telegram_bot5
Telegram bot with which we can order food


# Shop Bot
## A Telegram shop bot.

### Installation

You can install the necessary dependencies using pip:

```
pip install requirements.txt
```

You will also need to create a .env file in the root directory of your project and insert your Telegram and Vkontakte bot tokens:

```
DATABASE_PASSWORD=WzTn5YXxs9GBKmTagIumPT6G3WwiiRGS
DATABASE_HOST=redis-18165.c93.us-east-1-3.ec2.cloud.redislabs.com
DATABASE_PORT=18165
TELEGRAM_TOKEN=6256992603:AAFQYCDEsxdNUM4QpHfkIf1CXnm6tyANyDI
PRICE_BOOK_ID=70ff79b8-63c6-4931-a2ed-b56ca1900b3b
CART_ID=48353b61-fe15-43cf-b074-ed0d34928ce4
BEARER=f9b5246b1cc858e83d60a69fcc8fee88e5c82f41
```

### Usage

To start the bot, simply run the bot.py file:
```shell
python main.py
```


Once the bot is running, you can use the following command:

* /start - start the purchase
