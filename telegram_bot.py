import logging
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from functools import partial
from load_questions import load_questions
import random

logger = logging.getLogger(__name__)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    '''user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )'''
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет', ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Здравствуйте!', reply_markup=reply_markup)

def new_question(update: Update, context: CallbackContext, questions) -> None:
    """Send a new question when 'Новый вопрос' is issued."""
    question, answer = random.choice(questions)
    update.message.reply_text(question)

def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

    questions = list(load_questions().items())

    updater = Updater(telegram_token, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    new_question_handler = partial(new_question, questions=questions)
    dispatcher.add_handler(MessageHandler(Filters.regex('^Новый вопрос$'), new_question_handler))

    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()

    logger.info('Telegram bot started')

    updater.idle()


if __name__ == '__main__':
    main()
