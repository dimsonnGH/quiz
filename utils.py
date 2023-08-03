import os


def read_files(file_paths):
    text = ""
    for file_path in file_paths:
        with open(file_path, "r", encoding="KOI8-R") as file:
            text += file.read()
    return text


def example_load_questions(path_to_questions_folder):
    file_paths = [
        os.path.join(path_to_questions_folder, file_name)
        for file_name in os.listdir(path_to_questions_folder)
    ]

    files_content = read_files(file_paths)

    text_lines = files_content.split('\n\n')
    questions = {}

    for index, text_line in enumerate(text_lines):
        if 'Вопрос' in text_line:
            question = text_line.split(':')[1].replace('\n', ' ')
            answer = text_lines[index + 1].split(':')[1].replace('\n', '')
            questions[question] = answer
    return questions


def old_load_questions():
    file_path = r'C:\Python projects\dvmn\quiz\quiz-questions\aaron16.txt'
    with open(file_path, 'r', encoding='KOI8-R') as questions_file:
        file_contents = questions_file.read()

    paragraphs = file_contents.split('\n\n')
    question_list = [' '.join(paragraph.split('\n')[1:]) for paragraph in paragraphs if paragraph.startswith('Вопрос')]
    answer_list = [' '.join(paragraph.split('\n')[1:]) for paragraph in paragraphs if paragraph.startswith('Ответ')]
    comment_list = [' '.join(paragraph.split('\n')[1:]) for paragraph in paragraphs if paragraph.startswith('Комментарий')]
    questions = dict(zip(question_list, answer_list))

    return questions

def get_paragraph_content(paragraph):

    content = ' '.join(paragraph.split('\n')[1:])

    return content

def load_questions():
    file_path = r'C:\Python projects\dvmn\quiz\quiz-questions\aaron16.txt'
    with open(file_path, 'r', encoding='KOI8-R') as questions_file:
        file_contents = questions_file.read()

    paragraphs = file_contents.split('\n\n')

    questions = {}

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

"""if __name__ == '__main__':
    main()
    path_to_questions_folder = r'C:\Python projects\dvmn\quiz\test'
    load_questions(path_to_questions_folder)"""
