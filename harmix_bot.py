import json
import os
from pprint import pprint

import requests
import telebot
import telegram
from telebot import types

from additional_functions import delete_video, improve_and_upload_buttons, send_typing_action, create_users_data_dir, \
    send_other_musics, create_user_answers
from config_api import API_TOKEN, upload_url, combine_url
from harmix_db.main import update_sql, start_collect_user_data, insert_sql
from language_functions import phrase_on_language

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message):
    create_users_data_dir(message)
    bot.send_message(message.chat.id, " Hello! I'm Harmix bot.\n"
                                      "I can help you to choose the music for your video.")
    username = create_username_for_db(message)

    start_collect_user_data(username)
    choose_language_buttons(message)


@bot.message_handler(content_types=['video'])
def get_video(message):
    # delete musics_for_video dir if it exists to start work with a new video
    user_chat_id = str(message.chat.id)
    audios_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, 'musics_for_video')

    try:
        language_phrases = phrase_on_language(message, 'get_video_less_20')
        error_phrases = phrase_on_language(message, 'send_video_to_user')

    except:
        create_users_data_dir(message)
        language_phrases = phrase_on_language(message, 'get_video_less_20')
        error_phrases = phrase_on_language(message, 'send_video_to_user')

    try:
        if os.listdir(audios_path):
            for the_file in os.listdir(audios_path):
                file_path = os.path.join(audios_path, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)

    except:
        print('musics_for_video dir is empty')

    try:
        file_id = message.video.file_id
        # check a size of the video
        if message.video.file_size <= 20 * 10 ** 6:
            file_info = bot.get_file(file_id)
            bot.send_message(message.chat.id, language_phrases[0])

            # mkdir for special user
            path = "users_data/{}".format(user_chat_id)
            try:
                os.mkdir(path)
            except OSError:
                print("Creation of the directory %s failed or this directory exists" % path)
            else:
                print("Successfully created the directory %s " % path)

            downloaded_file = bot.download_file(file_info.file_path)

            # trying to change directory and download a video to user's dir
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
            with open(full_file_path + '.mp4', 'wb') as new_file:
                new_file.write(downloaded_file)

        else:
            bot.send_message(message.chat.id, language_phrases[1])
    except:
        print('get_video error - file_id = message.video.file_id or '
              'downloaded_file = bot.download_file(file_info.file_path or new_file.write(downloaded_file))')
        bot.send_message(message.chat.id, error_phrases[4])


@bot.message_handler(commands=['change_language'])
def choose_language_buttons(message):
    """
    :return: a keyboard with languages to change
    """

    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.row(
        telebot.types.InlineKeyboardButton('🇺🇦 Українська', callback_data='ua')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('🇺🇸 English', callback_data='uk')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('🇷🇺 Русский', callback_data='ru')
    )

    bot.send_message(message.chat.id, 'Choose a language that will be convenient for you to interact with our bot:\n\n'
                                      'You can change it at any time using /change_language command.',
                     reply_markup=keyboard)


@bot.message_handler(commands=['start_survey'])
def survey_buttons(message):
    """
    :return: a button to start a survey
    """
    try:
        language_phrase = phrase_on_language(message, "survey_buttons")
    except:
        create_users_data_dir(message)
        language_phrase = phrase_on_language(message, "survey_buttons")

    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.row(
        telebot.types.InlineKeyboardButton(language_phrase[0], callback_data='survey')
    )

    bot.send_message(message.chat.id, '📨📈📊 ' + language_phrase[1],
                     reply_markup=keyboard)


def keyboard_buttons_survey(message, question):
    try:
        language_answers_button = phrase_on_language(message, "answers")
        questions = phrase_on_language(message, 'questions')
    except:
        create_users_data_dir(message)
        language_answers_button = phrase_on_language(message, "answers")
        questions = phrase_on_language(message, 'questions')

    n_question = questions.index(question)
    keyboard = telebot.types.InlineKeyboardMarkup()

    for i in range(len(language_answers_button)):
        keyboard.row(
            telebot.types.InlineKeyboardButton(language_answers_button[i],
                                               callback_data=language_answers_button[i] + str(n_question))
        )

    bot.send_message(message.chat.id, question,
                     reply_markup=keyboard)


def start_survey(message, n_question=0):
    """

    :return: start every new question for user
    """
    try:
        user_chat_id = str(message.chat.id)
    except:
        user_chat_id = str(message.message.chat.id)

    try:
        questions = phrase_on_language(message, 'questions')
    except:
        create_users_data_dir(message)
        questions = phrase_on_language(message, 'questions')

    try:
        n_question = int(message.data[-1]) + 1
        message = message.message
    except:
        pass

    if n_question == 0:
        keyboard_buttons_survey(message, questions[n_question])
        full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
        with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
            file_user_data = json.load(f)
            file_user_data['survey_answers'] = []

        with open(full_file_path + "_data" + ".json", "w") as f:
            json.dump(file_user_data, f, ensure_ascii=False)

    # if the question need buttons to answer
    elif n_question == 1:
        keyboard_buttons_survey(message, questions[n_question])

    # after last question - print thank you
    elif n_question >= 4:
        msg_thanks = phrase_on_language(message, 'start_survey')
        bot.send_message(message.chat.id, '😄👍 ' + msg_thanks)
        upload_new_video = phrase_on_language(message, 'start_message')
        bot.send_message(message.chat.id, upload_new_video)

        # add user answers to user_chat_id + '_data' to input them in db
        username = create_username_for_db(message)
        try:
            user_chat_id = str(message.chat.id)
        except:
            user_chat_id = str(message.from_user.id)

        full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
        with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
            file_user_data = json.load(f)
            file_user_data['survey_answers'] = file_user_data.get('survey_answers', [])
            insert_sql('answers_on_survey', [username] + file_user_data['survey_answers'])

        try:
            # send json to admins
            full_file_path = os.path.join(os.getcwd(), 'templates', "answers_on_survey")
            with open(full_file_path + ".json", "r", encoding='utf-8') as answers_doc:
                denys_chat_id = 511986933
                bot.send_document(denys_chat_id, answers_doc, caption="Answer document")

            with open(full_file_path + ".json", "r", encoding='utf-8') as answers_doc:
                nazar_chat_id = 347963763
                bot.send_document(nazar_chat_id, answers_doc, caption="Answer document")

        except:
            print('start_survey error - # send json to admins')

    # if user writes answer without buttons
    elif n_question < 4:
        answer = bot.send_message(message.chat.id, questions[n_question])
        bot.register_next_step_handler(answer, answers_in_dict, n_question)


def create_username_for_db(message):
    # update data in answers_on_survey table SQL
    user_info = message.from_user
    if 'harmix_bot' == user_info.username or 'test_h_799_bot' == user_info.username:
        user_info = message.chat
    if user_info.username is None:
        if user_info.last_name is None:
            username = user_info.first_name
        else:
            username = user_info.first_name + ' ' + user_info.last_name
    else:
        username = '@' + user_info.username
    return username


def answers_in_dict_from_buttons(answer):
    """

    :param answer: a callback from buttons of the question
    :return: write answer in answers_on_survey.json to analys all comments of users on the survey
    """
    full_phrases_path = os.path.join(os.getcwd(), 'templates', 'phrases')
    language_answers = phrase_on_language(answer, 'answers')

    with open(full_phrases_path + ".json", "r", encoding="utf-8") as f:
        phrases = json.load(f)
        ru_answers = phrases['answers']['ru']
        ru_questions = phrases['questions']['ru']

    # n_question is the last digit from answer that I added in keyboard_buttons_survey function in callback
    n_question = 0
    try:
        n_question = int(answer.data[-1])
    except:
        pass

    ru_question = ru_questions[n_question]

    answer_text = ''
    try:
        answer_text = answer.data
    except:
        pass

    answer_text = answer_text[:len(answer_text) - 1]
    full_survey_answer_path = os.path.join(os.getcwd(), 'templates', 'answers_on_survey')

    try:
        with open(full_survey_answer_path + ".json", "r", encoding='utf-8') as f:
            survey_dict = json.load(f)
            try:
                if answer_text in language_answers:
                    ru_answer = ru_answers[language_answers.index(answer_text)]
                    survey_dict[ru_question][ru_answer] += 1

                    # update data in answers_on_survey table SQL
                    create_user_answers(answer, ru_answer)
                    with open(full_survey_answer_path + ".json", "w", encoding='utf-8') as f:
                        json.dump(survey_dict, f, ensure_ascii=False, indent=4)

                    # update_sql('answers_on_survey', 'question' + str(n_question + 1), username, ru_answer)

            except:

                with open(full_phrases_path + ".json", "r", encoding='utf-8') as f:
                    phrases = json.load(f)
                    language_answers = phrases['answers']['uk']

                if answer_text in language_answers:
                    ru_answer = ru_answers[language_answers.index(answer_text)]
                    survey_dict[ru_question][ru_answer] += 1

                    # update data in answers_on_survey table SQL
                    create_user_answers(answer, ru_answer)

                with open(full_survey_answer_path + ".json", "w", encoding='utf-8') as f:
                    json.dump(survey_dict, f, ensure_ascii=False, indent=4)

    except:
        print('answers_in_dict_from_buttons error - if answer_text in language_answers: or'
              ' json.dump(survey_dict, f, ensure_ascii=False, indent=4)')

    if n_question < 2:
        start_survey(answer, n_question + 1)


def answers_in_dict(answer, n_question):
    """

   :param answer: user answer without buttons
   :return: write answer in answers_on_survey.json to analys all comments of users on the survey
   """
    full_phrases_path = os.path.join(os.getcwd(), 'templates', 'phrases')

    try:
        with open(full_phrases_path + ".json", "r", encoding="utf-8") as f:
            phrases = json.load(f)
            ru_questions = phrases['questions']['ru']

        ru_question = ru_questions[n_question]

        full_phrases_path = os.path.join(os.getcwd(), 'templates', 'answers_on_survey')
        with open(full_phrases_path + ".json", "r", encoding='utf-8') as f:
            survey_dict = json.load(f)

            # update data in answers_on_survey table SQL
            username = create_username_for_db(answer)
            user_answer = username + ':   ' + answer.text
            survey_dict[ru_question].append(user_answer)
            create_user_answers(answer, answer.text)
            # update_sql('answers_on_survey', 'question' + str(n_question + 1), username, answer.text)

        with open(full_phrases_path + ".json", "w", encoding='utf-8') as f:
            json.dump(survey_dict, f, ensure_ascii=False, indent=4)

    except:
        print('answers_in_dict error - ru_questions = phrases[\'questions\'][\'ru\']'
              ' or update_sql(\'answers_on_survey\',')

    # give a new question
    start_survey(answer, n_question + 1)


@bot.message_handler(commands=['upload_new_video'])
def upload_new_video(message):
    try:
        language_phrases = phrase_on_language(message, "take_input")

    except:
        create_users_data_dir(message)
        language_phrases = phrase_on_language(message, "take_input")

    bot.send_message(message.chat.id, language_phrases[1], disable_notification=True)


@bot.message_handler(content_types=['text'])
def get_text(message):
    # if user choose the same parameter in keyboard like ✅Enable
    if message.text.startswith("✅"):
        message.text = message.text[1:]

    user_chat_id = str(message.chat.id)
    error_phrases = phrase_on_language(message, 'send_video_to_user')

    # answer on Are you sure that you want to upload this video? (Type YES/NO)
    yes_lst = ["YES", "ТАК", "ДА"]
    no_lst = ["NO", "НІ", "НЕТ"]
    try:
        language_phrases = phrase_on_language(message, 'get_text')
    except:
        create_users_data_dir(message)
        language_phrases = phrase_on_language(message, 'get_text')

    try:
        ready_ans = message.text.strip().upper()
        if ready_ans in yes_lst:
            bot.send_message(message.from_user.id, '🤖🔁🎞↪️🎶 ' + language_phrases[0])
            adapt_video(message)

        elif ready_ans in no_lst:
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id)

            # If the file exists, delete it
            try:
                os.remove(os.path.join(full_file_path, '{}.mp4'.format(user_chat_id)))
            except:
                print('downloaded_video does not exist')

            language_phrases = phrase_on_language(message, "start_message")
            bot.send_message(message.chat.id, language_phrases)

        else:
            try:
                # take text parameter for changing from user and send it to new keyboard
                full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

                data = json.load(open(full_file_path + ".json", "r", encoding="utf-8"))
                parameters = ["genre", 'mood', 'instrument', 'vocal', 'fade_effects']

                # find a list of parameters with special user language
                language_parameters = phrase_on_language(message, "parameters")
                full_phrases_path = os.path.join(os.getcwd(), 'templates', 'phrases')

                try:
                    with open(full_phrases_path + ".json", "r", encoding="utf-8") as f:
                        phrases = json.load(f)
                        dict_uk_choices = phrases['choices']['uk']

                except:
                    print('get_text error - dict_uk_choices = phrases[\'choices\'][\'uk\']')

                dict_language_choices = phrase_on_language(message, 'choices')

                changed_parameter = ''

                # like a parameter for "vocal" and "fade effects"
                vocal_marks = phrase_on_language(message, 'vocal_marks')
                if message.text == vocal_marks[1]:
                    message.text = '0'

                elif message.text == vocal_marks[2]:
                    message.text = '1'

                elif message.text == vocal_marks[0]:
                    message.text = '0.5'

                for key in dict_language_choices:
                    if message.text in dict_language_choices[key]:
                        flag_message_in_choices = 1
                        changed_parameter = str(key)
                        break

                # if user change parameter and buttons appear second time -
                # if input_parameter 'vocal' then message.text in int and then input in data.json
                if flag_message_in_choices == 1:
                    position_uk_parameter = language_parameters.index(changed_parameter)
                    uk_parameter = parameters[position_uk_parameter]

                    if message.text[-1].isdigit():
                        if message.text == '0.5':
                            data[uk_parameter] = 0.5
                        else:
                            data[uk_parameter] = int(message.text)
                    else:
                        position = dict_language_choices[changed_parameter].index(message.text)
                        if message.text in ['Enable', "Увімкнені", "Включенные"]:
                            data[uk_parameter] = 1
                        elif message.text in ['Disable', "Вимкнені", "Выключенные"]:
                            data[uk_parameter] = 0
                        else:
                            data[uk_parameter] = dict_uk_choices[uk_parameter][position]

                    try:
                        with open(full_file_path + ".json", "w", encoding='utf-8') as f:
                            json.dump(data, f)

                    except:
                        print('get_text error - dict_uk_choices = phrases[\'choices\'][\'uk\']')
                        bot.send_message(message.chat.id, error_phrases[4])

                    change_parameters_buttons(message)

                elif flag_message_in_choices != 1:
                    bot.send_message(message.chat.id,
                                     language_phrases[1])

            except:
                bot.send_message(message.chat.id, language_phrases[1])

    except:
        bot.send_message(message.chat.id, "Something went wrong, please upload your video again")


@send_typing_action
def adapt_video(message):
    """

    :return: post to server, get json and, if user wish, change parameters with keyboard
    """
    user_chat_id = str(message.chat.id)
    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
    error_phrases = phrase_on_language(message, 'send_video_to_user')

    try:
        # Open video and send POST with video to server
        with open(full_file_path + '.mp4', 'rb') as video_file:
            file_ = {'file': (full_file_path + '.mp4', video_file)}
            upload_response = requests.post(upload_url, files=file_)

        # Get json and, if user wish, change parameters
        data = json.loads(upload_response.text)
        # """
        data["genre"] = "Any genre"
        data["mood"] = "Any mood"
        data["instrument"] = "Any instrument"
        data["vocal"] = 0.5
        # """
        data["fade_effects"] = 0
        data["selected_music"] = 0
        with open(full_file_path + ".json", "w") as f:
            json.dump(data, f)

    except:
        print('adapt_video error - upload_response = requests.post(upload_url, files=file_) '
              'or json.dump(data, f)')
        bot.send_message(message.chat.id, error_phrases[4])

    skip_flag = 1
    change_parameters_buttons(message, skip_flag)


def send_video_to_user(message):
    bot.send_chat_action(message.chat.id, 'upload_video')
    user_chat_id = str(message.chat.id)
    error_phrases = phrase_on_language(message, 'send_video_to_user')
    try:
        language_phrases = phrase_on_language(message, 'send_video_to_user')
    except:
        create_users_data_dir(message)
        language_phrases = phrase_on_language(message, 'send_video_to_user')

    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

    try:
        with open(full_file_path + ".json", "r") as f:
            data = json.load(f)

        # post json file with parameters changed by user and send it to user
        combine_response = requests.post(combine_url, json=data)
        binary_string = combine_response.content

        with open(full_file_path + 'downloaded_video_{}.mp4'.format(user_chat_id), 'wb') as video_file:
            video_file.write(binary_string)

        # a json of 5 musics that also can be special for this video
        music_data = json.loads(combine_response.headers['X-Extra-Info-JSON'])

        with open(full_file_path + 'musics5_for_video' + ".json", 'w') as musics5_file:
            json.dump(music_data, musics5_file, indent=4)

    except:
        print('send_video_to_user error - data = json.load(f) or video_file.write(binary_string) '
              'or json.dump(music_data, musics5_file, indent=4)')
        bot.send_message(message.chat.id, error_phrases[4])

    file_size = 0
    path = full_file_path + 'downloaded_video_{}.mp4'.format(user_chat_id)
    # Get the size (in bytes)
    # of specified path
    try:
        try:
            file_size = os.path.getsize(path)
        except:
            print("Path '%s' does not exists or is inaccessible" % path)

        try:
            if file_size < 2 * 10 ** 7 and file_size != 0:
                with open(path, 'rb') as video:
                    bot.send_message(message.chat.id, '🆕🎬 ' + language_phrases[0])
                    bot.send_video(message.chat.id, video, caption=language_phrases[1],
                                   parse_mode=telegram.ParseMode.HTML, disable_notification=True)

            delete_video(message)
            improve_and_upload_buttons(message)

            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
            with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
                file_user_data = json.load(f)
                file_user_data["n_videos"] = file_user_data.get("n_videos", 0) + 1

                # data in users_data table
                username = create_username_for_db(message)
                update_sql('users_data', 'n_videos', username, file_user_data["n_videos"])

            with open(full_file_path + "_data" + ".json", "w") as f:
                json.dump(file_user_data, f)

        except:
            print('send_video_to_user error -  json.dump(file_user_data, f) '
                  'or update_sql(\'users_data\', \'n_videos\', username, file_user_data["n_videos"]) or'
                  'file_user_data["n_videos"] = file_user_data.get("n_videos", 0) + 1')
            bot.send_message(message.chat.id, error_phrases[4])

        try:
            if file_user_data["n_videos"] == 3:
                survey_buttons(message)
        except:
            pass

    except:
        bot.send_message(message.chat.id, language_phrases[3])


@send_typing_action
def change_parameters_buttons(message, skip_flag=0):
    """
    :return: a keyboard with video  or changed by user parameters
    """
    user_chat_id = str(message.chat.id)
    error_phrases = phrase_on_language(message, 'send_video_to_user')
    try:
        button_parameters = phrase_on_language(message, 'parameters')
        vocal_marks = phrase_on_language(message, 'vocal_marks')
        fade_marks = phrase_on_language(message, 'fade_marks')
    except:
        create_users_data_dir(message)
        button_parameters = phrase_on_language(message, 'parameters')
        vocal_marks = phrase_on_language(message, 'vocal_marks')
        fade_marks = phrase_on_language(message, 'fade_marks')

    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

    keyboard = telebot.types.InlineKeyboardMarkup()
    data = dict()
    try:
        data = json.load(open(full_file_path + ".json", "r", encoding="utf-8"))

    except:
        print('change_parameters_buttons error -  data = json.load(open(full_file_path ')
        bot.send_message(message.chat.id, error_phrases[4])

    parameters = ["genre", 'mood', 'instrument', 'vocal', "fade_effects"]
    vocal_mark = ''

    # for change vocal on Lyrics and 0 or other digits on "Any lyrics", "Without lyrics", "With lyrics"
    # for print it in buttons for user(the same for fade_effects)
    if data['vocal'] == 0:
        vocal_mark = vocal_marks[1]

    elif data['vocal'] == 1:
        vocal_mark = vocal_marks[2]

    elif data['vocal'] == 0.5:
        vocal_mark = vocal_marks[0]

    fade_mark = ''
    if data['fade_effects'] == 0:
        fade_mark = fade_marks[0]

    elif data['fade_effects'] == 1:
        fade_mark = fade_marks[1]

    full_phrases_path = os.path.join(os.getcwd(), 'templates', 'phrases')
    with open(full_phrases_path + ".json", "r", encoding="utf-8") as f:
        phrases = json.load(f)
        dict_uk_choices = phrases['choices']['uk']

    dict_language_choices = phrase_on_language(message, 'choices')

    for parameter in parameters:
        pos = parameters.index(parameter)
        language_parameter = button_parameters[pos]
        button_parameter = language_parameter[0].upper() + language_parameter[1:]
        if button_parameter == 'Fade_effects':
            button_parameter = 'Fade effects'

        if parameter == 'vocal':
            if language_parameter in dict_uk_choices["vocal"]:
                button_parameter = 'Lyrics'

            keyboard.row(
                telebot.types.InlineKeyboardButton('{0}: {1}'.format(button_parameter, vocal_mark),
                                                   callback_data=parameter)
            )

        elif parameter == 'fade_effects':
            keyboard.row(
                telebot.types.InlineKeyboardButton('{0}: {1}'.format(button_parameter, fade_mark),
                                                   callback_data=parameter)
            )
        else:
            position = dict_uk_choices[parameter].index(data[parameter])
            keyboard.row(
                telebot.types.InlineKeyboardButton('{0}: {1}'.format(button_parameter,
                                                                     dict_language_choices[language_parameter][
                                                                         position]),
                                                   callback_data=parameter)
            )

    # if parameters buttons appear first or after sent adapt video than add SKIP button
    if skip_flag == 1:
        language_phrases = phrase_on_language(message, 'next')
        keyboard.row(
            telebot.types.InlineKeyboardButton('⏩ ' + language_phrases[0], callback_data='Next')
        )

        language_phrases = phrase_on_language(message, 'change_parameters_buttons')
        msg_buttons = bot.send_message(message.chat.id, '💡🎨🎼 ' + language_phrases,
                         reply_markup=keyboard)

    # if parameters buttons appear not first or after sent adapt video than add CONTINUE button
    else:
        language_phrases = phrase_on_language(message, 'next')
        keyboard.row(
            telebot.types.InlineKeyboardButton('➡️ ' + language_phrases[1], callback_data='Next')
        )

        try:
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
            with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
                file_user_data = json.load(f)
                chat_id = file_user_data['chat_id_buttons']
                message_id = file_user_data['message_id_buttons']
                bot.delete_message(chat_id, message_id)

        except Exception:
            pass

        language_phrases = phrase_on_language(message, 'change_parameters_buttons')
        msg_buttons = bot.send_message(message.chat.id, '💡🎨🎼 ' + language_phrases,
                         reply_markup=keyboard)

    # save message_id of msg_buttons in user_id_data.json to delete this message when new buttons arise
    try:
        full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
        with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
            file_user_data = json.load(f)
            message_id = msg_buttons.message_id
            file_user_data['message_id_buttons'] = message_id
            file_user_data['chat_id_buttons'] = message.chat.id

        with open(full_file_path + "_data" + ".json", "w") as f:
            json.dump(file_user_data, f)

    except:
        print('change_parameters_buttons error -   file_user_data[\'message_id_buttons\'] = message_id')


@bot.callback_query_handler(func=lambda call: True)
def take_input(query):
    """

    :param query: a data from  buttons function that is in callback
    """
    data = query.data
    try:
        language_phrases = phrase_on_language(query.message, "take_input")

    except:
        create_users_data_dir(query.message)
        language_phrases = phrase_on_language(query.message, "take_input")

    error_phrases = phrase_on_language(query.message, 'send_video_to_user')
    user_chat_id = str(query.message.chat.id)

    if data == 'Next':
        bot.send_message(query.message.chat.id, language_phrases[0])
        send_video_to_user(query.message)

    # to take language that chose user and write in user_data.json
    elif (data == "ua") or (data == "ru") or (data == "uk"):
        user_chat_id = str(query.message.chat.id)

        try:
            # trying to change directory and download a video to user's dir
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
            try:
                with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
                    file_user_data = json.load(f)
                    file_user_data['language'] = data

                with open(full_file_path + "_data" + ".json", "w") as f:
                    json.dump(file_user_data, f)
            except:
                string = '{"language": "' + data + '"}'
                user_data = json.loads(string)
                with open(full_file_path + "_data" + ".json", "w") as f:
                    json.dump(user_data, f)

        except:
            # trying to change directory and download a video to user's dir
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
            try:
                with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
                    file_user_data = json.load(f)
                    file_user_data['language'] = data

                with open(full_file_path + "_data" + ".json", "w") as f:
                    json.dump(file_user_data, f)
            except:
                create_users_data_dir(query.message)
                string = '{"language": "' + data + '"}'
                user_data = json.loads(string)
                with open(full_file_path + "_data" + ".json", "w") as f:
                    json.dump(user_data, f)

        # update data in users_data table
        username = create_username_for_db(query.message)
        update_sql('users_data', 'language', username, data)

        language_phrases = phrase_on_language(query.message, "start")
        bot.send_message(query.message.chat.id, language_phrases)

    elif data == 'survey':
        start_survey(query.message)

    elif data == 'improve':
        send_other_musics(query.message)

    elif data == 'change_music_params':
        change_parameters_buttons(query.message)

    elif data == 'upload_video2':
        bot.send_message(query.message.chat.id, language_phrases[1], disable_notification=True)

    elif data.startswith('audio_'):
        try:
            language_phrases = phrase_on_language(query.message, "get_text")

        except:
            create_users_data_dir(query.message)
            language_phrases = phrase_on_language(query.message, "get_text")

        bot.send_message(query.message.chat.id, language_phrases[0], disable_notification=True)

        user_chat_id = str(query.message.chat.id)
        full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

        try:
            with open(full_file_path + '.json', 'r') as json_about_video:
                video_data = json.loads(json_about_video.read())

            video_data["selected_music"] = int(data[-1])
            with open(full_file_path + ".json", "w") as f:
                json.dump(video_data, f)

            send_video_to_user(query.message)
        except:
            print('take_input error -  video_data = json.loads(json_about_video.read())')
            bot.send_message(query.message.chat.id, error_phrases[4])

    # send query to other function to write answer on questions with buttons in json
    elif data[-1].isdigit():
        answers_in_dict_from_buttons(query)
    else:
        type_keyboard(query.message, data)


def type_keyboard(message, data):
    """
    :return: make a keyboard of different lists of parameters ("genre", 'mood', 'instrument', 'vocal', 'fade_effects')
    """
    error_phrases = phrase_on_language(message, 'send_video_to_user')

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    full_phrases_path = os.path.join(os.getcwd(), 'templates', 'phrases')
    with open(full_phrases_path + ".json", "r", encoding="utf-8") as f:
        phrases = json.load(f)
        dict_uk_choices = phrases['choices']['uk']

    parameters = ["genre", 'mood', 'instrument', 'vocal', 'fade_effects']

    # find a list of parameters with special user language
    pos = parameters.index(data)
    try:
        language_parameters = phrase_on_language(message, "parameters")
        dict_language_choices = phrase_on_language(message, 'choices')
    except:
        create_users_data_dir(message)
        language_parameters = phrase_on_language(message, "parameters")
        dict_language_choices = phrase_on_language(message, 'choices')

    type_list = dict_language_choices[language_parameters[pos]]
    uk_type_list = dict_uk_choices[parameters[pos]]
    if data == 'vocal':
        type_list = phrase_on_language(message, 'vocal_marks')

    elif data == 'fade_effects':
        type_list = phrase_on_language(message, 'fade_marks')

    user_chat_id = str(message.chat.id)
    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

    try:
        with open(full_file_path + ".json", "r") as f:
            file_data = json.load(f)
    except:
        print('type_keyboard error -  file_data = json.load(f)')
        bot.send_message(message.chat.id, error_phrases[4])

    vocal_mark, fade_mark = '', ''
    for i, type_input in enumerate(type_list):
        # change parameter from user_video.json from 0 or 1 on words to input it in buttons
        if data in ['vocal', 'вокал']:
            vocal_mark = file_data[data]
            vocal_marks = phrase_on_language(message, 'vocal_marks')

            if vocal_mark == 0:
                vocal_mark = vocal_marks[1]

            elif vocal_mark == 0.5:
                vocal_mark = vocal_marks[0]

            elif vocal_mark == 1:
                vocal_mark = vocal_marks[2]

        elif data == 'fade_effects':
            fade_mark = file_data[data]
            fade_marks = phrase_on_language(message, 'fade_marks')

            if fade_mark == 0:
                fade_mark = fade_marks[0]

            elif fade_mark == 1:
                fade_mark = fade_marks[1]

        if type_input == vocal_mark:
            type_input = '✅' + type_input

        elif type_input == fade_mark:
            type_input = '✅' + type_input

        elif file_data[data] == uk_type_list[i]:
            type_input = '✅' + type_input

        markup.add(type_input)  # Names of buttons

    language_phrase = phrase_on_language(message, "type_keyboard")
    bot.send_message(message.chat.id, language_phrase, reply_markup=markup)


if __name__ == "__main__":
    bot.polling()
