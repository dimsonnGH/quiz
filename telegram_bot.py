import logging
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from functools import partial
from load_questions import load_questions
import random
import redis

logger = logging.getLogger(__name__)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def check_answer(update: Update, context: CallbackContext, questions, redis_db) -> None:
    """"""
    user_answer = update.message.text.lower()
    question = redis_db.get(update.effective_user.id)
    question_details = questions[question]
    correct_answer = question_details['answer'].lower()

    if user_answer in correct_answer:
        if question_details["comment"]:
            reply_text = f'Правильно\n{question_details["comment"]}'
        else:
            reply_text = 'Правильно'
        custom_keyboard = [['Новый вопрос',]]
    else:
        reply_text = 'Не правильно'
        custom_keyboard = [['Сдаться',]]

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(reply_text, reply_markup=reply_markup)


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

def new_question(update: Update, context: CallbackContext, questions, redis_db) -> None:
    """Send a new question when 'Новый вопрос' is issued."""
    #question, answer = random.choice(questions)
    question = random.choice(questions)
    update.message.reply_text(question)

    #print(f'1. {redis_db.get(update.effective_user.id)}')

    redis_db.set(update.effective_user.id, question)
    #redis_db.set(update.effective_user.id, 'гыгы')
    #redis_db.set('бубу', 'гыгы')

    #print(f'2. {redis_db.get(update.effective_user.id)}')
    #print(redis_db.get('бубу'))

def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

    redis_db = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=1, charset='utf-8', decode_responses=True)

    #questions = list(load_questions().items())
    questions = load_questions()
    question_list = list(questions)

    updater = Updater(telegram_token, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    new_question_handler = partial(new_question, questions=question_list, redis_db=redis_db)
    dispatcher.add_handler(MessageHandler(Filters.regex('^Новый вопрос$'), new_question_handler))

    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    check_answer_handler = partial(check_answer, questions=questions, redis_db=redis_db)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer_handler))

    updater.start_polling()

    logger.info('Telegram bot started')

    updater.idle()


if __name__ == '__main__':
    main()
