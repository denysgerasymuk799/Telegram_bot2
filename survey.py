import telebot
from additional_functions import create_users_data_dir
from language_functions import phrase_on_language
from config_api import API_TOKEN


bot = telebot.TeleBot(API_TOKEN)


def survey_buttons(message):
    """
    :return: a button starting a survey
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

    bot.send_message(message.chat.id, language_phrase[1],
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
            telebot.types.InlineKeyboardButton(language_answers_button[i], callback_data=language_answers_button[i] + str(n_question))
        )

    bot.send_message(message.chat.id, question,
                     reply_markup=keyboard)
