import logging

from telegram.ext import ApplicationBuilder

from config import TOKEN
from handlers import setup_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    setup_handlers(app)
    app.run_polling()


if __name__ == '__main__':
    main()