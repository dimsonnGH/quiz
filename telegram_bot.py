import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from functools import partial
import utils
import random
import redis

logger = logging.getLogger(__name__)

CHOICE, ANSWER = range(2)


def check_answer(update: Update, context: CallbackContext, questions, redis_db):
    user_answer = update.message.text
    user_id = update.effective_user.id
    is_correct, comment = utils.check_answer(user_answer, user_id, questions, redis_db)

    if is_correct:
        if comment:
            reply_text = f'Правильно\n{comment}'
        else:
            reply_text = 'Правильно'
        custom_keyboard = [['Новый вопрос', ]]
        state = CHOICE

    else:
        reply_text = 'Не правильно'
        custom_keyboard = [['Сдаться', ]]
        state = ANSWER

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(reply_text, reply_markup=reply_markup)

    return state


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""

    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет', ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Здравствуйте!', reply_markup=reply_markup)

    return CHOICE


def new_question(update: Update, context: CallbackContext, questions, redis_db):
    """Send a new question when 'Новый вопрос' is issued."""

    question = random.choice(questions)

    redis_db.set(update.effective_user.id, question)

    custom_keyboard = [['Сдаться', ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text(question, reply_markup=reply_markup)

    return ANSWER


def other_choice(update: Update, context: CallbackContext):
    """Return CHOICE state when 'Новый вопрос' isn't issued."""

    custom_keyboard = [['Новый вопрос', ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Продолжим?', reply_markup=reply_markup)

    return CHOICE


def end_game(update: Update, context: CallbackContext):
    """End the game."""

    update.message.reply_text("Игра окончена")

    return ConversationHandler.END


def skip_question(update: Update, context: CallbackContext, questions, question_list, redis_db):
    """Skip a question."""

    question = redis_db.get(update.effective_user.id)

    if not question:
        return CHOICE

    question_details = questions[question]

    reply_text = question_details["answer"]
    update.message.reply_text(reply_text)

    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет', ]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    reply_text = question_details["comment"]
    if reply_text:
        update.message.reply_text(reply_text, reply_markup=reply_markup)

    redis_db.delete(update.effective_user.id)

    return CHOICE


def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

    redis_db = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=1, charset='utf-8',
                           decode_responses=True)

    questions_folder_name = os.getenv("QUESTIONS_FOLDER_NAME", "questions")
    questions = utils.load_questions(questions_folder_name)
    question_list = list(questions)
    logger.info('questions are loaded')

    updater = Updater(telegram_token, use_context=True)

    dispatcher = updater.dispatcher

    new_question_handler = partial(new_question, questions=question_list, redis_db=redis_db)

    skip_question_handler = partial(skip_question, questions=questions, question_list=question_list, redis_db=redis_db)

    check_answer_handler = partial(check_answer, questions=questions, redis_db=redis_db)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOICE: [MessageHandler(Filters.regex('^[Нн]овый вопрос$'), new_question_handler),
                     MessageHandler(Filters.text, other_choice)
                     ],

            ANSWER: [MessageHandler(Filters.regex('^[Сс]даться$'), skip_question_handler),
                     MessageHandler(Filters.text & ~Filters.command, check_answer_handler)
                     ]
        },

        fallbacks=[MessageHandler(Filters.regex('^[Сс]даться$'), skip_question_handler)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    logger.info('Telegram bot started')

    updater.idle()


if __name__ == '__main__':
    main()
