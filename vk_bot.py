import random
from dotenv import load_dotenv
import os

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import questions_utils

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


def send_new_question(event, vk_api, questions, redis_db):
    """Send a new question when 'Новый вопрос' is issued."""

    question = random.choice(questions)

    user_id = event.user_id

    redis_db.set(user_id, question)

    keyboard = get_answer_keyboard()

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def check_answer(event, vk_api, questions, redis_db):
    user_answer = event.text
    user_id = event.user_id

    question_details = questions_utils.get_question_details(user_id, questions, redis_db)
    comment = question_details['comment']
    is_correct = questions_utils.check_answer(user_answer, question_details)

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
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def skip_question(event, vk_api, questions, redis_db):
    """Skip a question."""
    user_id = event.user_id

    question = redis_db.get(user_id)

    if not question:
        return

    question_details = questions[question]

    reply_text = question_details["answer"]
    if question_details["comment"]:
        vk_api.messages.send(
            user_id=user_id,
            message=reply_text,
            random_id=random.randint(1, 1000)
        )

        reply_text = f'{question_details["comment"]}'
        keyboard = get_keyboard()

        vk_api.messages.send(
            user_id=user_id,
            message=reply_text,
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )
    else:
        keyboard = get_keyboard()
        vk_api.messages.send(
            user_id=user_id,
            message=reply_text,
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )


if __name__ == "__main__":

    load_dotenv()

    vk_api_key = os.getenv("VK_API_KEY")

    vk_session = vk.VkApi(token=vk_api_key)
    vk_api = vk_session.get_api()

    redis_db = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=1, charset='utf-8',
                           decode_responses=True)

    questions_folder_name = os.getenv("QUESTIONS_FOLDER_NAME", "questions")
    questions = questions_utils.load_questions(questions_folder_name)
    question_keys = list(questions)

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            lower_text = event.text.lower()
            if lower_text == "новый вопрос":
                send_new_question(event, vk_api, question_keys, redis_db)
            elif lower_text == "сдаться":
                skip_question(event, vk_api, questions, redis_db)
            else:
                check_answer(event, vk_api, questions, redis_db)
