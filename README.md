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
DATABASE_PASSWORD=thisispasswordofdatabase
DATABASE_HOST=redisdatabasehost
DATABASE_PORT=12345
TELEGRAM_TOKEN=thisistelegramtoken
PRICE_BOOK_ID=thisispricebookid
CART_ID=thisiscartid
CLIENT_ID=thisisclientid
CLIENT_SECRET=thisisclientsecret
BEARER=f9b5246b1cc858e83d60a69fcc8fee88e5c82f41
```

### Usage

To start the bot, simply run the bot.py file:
```shell
python main.py
```


Once the bot is running, you can use the following command:

* /start - start the purchase
