import random
from dotenv import load_dotenv
import os

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import utils

import redis

def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счет')

    return keyboard

def get_answer_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    return keyboard
def echo(event, vk_api):

    keyboard = get_keyboard()

    vk_api.messages.send(
        user_id=event.user_id,
        message="ответ: " + event.text,
        random_id=random.randint(1,1000),
        keyboard = keyboard.get_keyboard()
    )
def send_new_question(event, vk_api, questions, redis_db):

    """Send a new question when 'Новый вопрос' is issued."""

    question = random.choice(questions)

    user_id = event.user_id

    redis_db.set(user_id, question)

    keyboard = get_answer_keyboard()

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=random.randint(1,1000),
        keyboard = keyboard.get_keyboard()
    )

def check_answer(event, vk_api, questions, redis_db):
    """"""
    user_answer = event.text
    user_id = event.user_id

    is_correct, comment = utils.check_answer(user_answer, event.user_id, questions, redis_db)

    if is_correct:
        if comment:
            reply_text = f'Правильно\n{comment}'
        else:
            reply_text = 'Правильно'
        keyboard = get_keyboard()
    else:
        reply_text = 'Не правильно'
        keyboard = get_answer_keyboard()

    vk_api.messages.send(
        user_id=user_id,
        message=reply_text,
        random_id=random.randint(1,1000),
        keyboard = keyboard.get_keyboard()
    )

def skip_question(event, vk_api, questions, redis_db):

    """Skip a question."""
    user_id = event.user_id

    question = redis_db.get(user_id)
    question_details = questions[question]

    reply_text = f'{question_details["comment"]}'
    keyboard = get_keyboard()

    vk_api.messages.send(
        user_id=user_id,
        message=reply_text,
        random_id=random.randint(1,1000),
        keyboard = keyboard.get_keyboard()
    )


if __name__ == "__main__":

    load_dotenv()

    vk_api_key = os.getenv("VK_API_KEY")

    vk_session = vk.VkApi(token=vk_api_key)
    vk_api = vk_session.get_api()

    redis_db = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=1, charset='utf-8', decode_responses=True)

    questions = utils.load_questions()
    question_list = list(questions)

    '''vk.messages.send(
        peer_id=123456,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message='Пример клавиатуры'
    )'''


    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            #echo(event, vk_api)
            if event.text == "Новый вопрос":
                send_new_question(event, vk_api, question_list, redis_db)
            elif event.text == "Сдаться":
                skip_question(event, vk_api, questions, redis_db)
            else:
                check_answer(event, vk_api, questions, redis_db)
