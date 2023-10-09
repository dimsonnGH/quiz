import os


def get_paragraph_content(paragraph):
    content = ' '.join(paragraph.split('\n')[1:])

    return content


def load_questions(folder_name):
    file_paths = [os.path.join(folder_name, file_name) for file_name in os.listdir(folder_name)]

    questions = {}

    for file_path in file_paths:
        with open(file_path, 'r', encoding='KOI8-R') as questions_file:
            file_contents = questions_file.read()

        paragraphs = file_contents.split('\n\n')

        answer_fields = {'answer': 'Ответ', 'comment': 'Комментарий'}
        fields = answer_fields.keys()
        question = ''
        for paragraph in paragraphs:
            if paragraph.startswith('Вопрос'):
                question = get_paragraph_content(paragraph)
                questions[question] = dict.fromkeys(fields, '')
            if question:
                for field, first_word in answer_fields.items():
                    if paragraph.startswith(first_word):
                        questions[question][field] = get_paragraph_content(paragraph)

    return questions


def check_answer(user_answer, user_id, questions, redis_db):
    """"""
    norm_user_answer = user_answer.lower()
    question = redis_db.get(user_id)
    question_details = questions[question]
    correct_answer = question_details['answer'].lower()

    comment = ""
    if norm_user_answer in correct_answer:
        result = True
        if question_details["comment"]:
            comment = question_details["comment"]
    else:
        result = False

    return (result, comment)
