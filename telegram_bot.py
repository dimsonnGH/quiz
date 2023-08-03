import logging
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from functools import partial
from utils import load_questions
import random
import redis

logger = logging.getLogger(__name__)

CHOICE, ANSWER = range(2)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def check_answer(update: Update, context: CallbackContext, questions, redis_db):
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
        state = CHOICE

    else:
        reply_text = 'Не правильно'
        custom_keyboard = [['Сдаться',]]
        state = ANSWER

    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(reply_text, reply_markup=reply_markup)

    return state



"""def start(update: Update, context: CallbackContext) -> None:"""
def start(update: Update, context: CallbackContext):
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

    return CHOICE

"""def new_question(update: Update, context: CallbackContext, questions, redis_db) -> None:"""
def new_question(update: Update, context: CallbackContext, questions, redis_db):

    """Send a new question when 'Новый вопрос' is issued."""

    question = random.choice(questions)

    redis_db.set(update.effective_user.id, question)

    update.message.reply_text(question)

    return ANSWER


"""def end_game(update: Update, context: CallbackContext) -> None:"""
def end_game(update: Update, context: CallbackContext):

    """End the game."""

    update.message.reply_text("Игра окончена")

    return ConversationHandler.END

def skip_question(update: Update, context: CallbackContext, questions, question_list, redis_db):

    """Skip a question."""

    question = redis_db.get(update.effective_user.id)
    question_details = questions[question]

    reply_text = f'{question_details["comment"]}'
    update.message.reply_text(reply_text)

    state = new_question(update, context, question_list, redis_db)

    return state

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

    """dispatcher.add_handler(CommandHandler("start", start))

    new_question_handler = partial(new_question, questions=question_list, redis_db=redis_db)
    dispatcher.add_handler(MessageHandler(Filters.regex('^Новый вопрос$'), new_question_handler))

    end_game_handler = partial(end_game)
    dispatcher.add_handler(MessageHandler(Filters.regex('^Сдаться$'), end_game_handler))

    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    check_answer_handler = partial(check_answer, questions=questions, redis_db=redis_db)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer_handler))"""

    new_question_handler = partial(new_question, questions=question_list, redis_db=redis_db)

    skip_question_handler = partial(skip_question, questions=questions, question_list=question_list, redis_db=redis_db)

    check_answer_handler = partial(check_answer, questions=questions, redis_db=redis_db)


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOICE: [MessageHandler(Filters.regex('^Новый вопрос$'), new_question_handler)],

            ANSWER: [MessageHandler(Filters.regex('^Сдаться$'), skip_question_handler),
                     MessageHandler(Filters.text & ~Filters.command, check_answer_handler)]
        },

        fallbacks=[] #[MessageHandler(Filters.regex('^Сдаться$'), end_game_handler)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    logger.info('Telegram bot started')

    updater.idle()


if __name__ == '__main__':
    main()
