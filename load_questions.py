import os


def read_files(file_paths):
    text = ""
    for file_path in file_paths:
        with open(file_path, "r", encoding="KOI8-R") as file:
            text += file.read()
    return text


def load_questions(path_to_questions_folder):
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


def main():
    # [Раздатка]
    file_path = r'C:\Python projects\dvmn\quiz\quiz-questions\aaron16.txt'
    with open(file_path, 'r', encoding='KOI8-R') as questions_file:
        file_contents = questions_file.read()

    paragraphs = file_contents.split('\n\n')
    question_list = [' '.join(paragraph.split('\n')[1:]) for paragraph in paragraphs if paragraph.startswith('Вопрос')]
    answer_list = [' '.join(paragraph.split('\n')[1:]) for paragraph in paragraphs if paragraph.startswith('Ответ')]
    questions = dict(zip(question_list, answer_list))

    a = 1


if __name__ == '__main__':
    main()
    '''path_to_questions_folder = r'C:\Python projects\dvmn\quiz\test'
    load_questions(path_to_questions_folder)'''
