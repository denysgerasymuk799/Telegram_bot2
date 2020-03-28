import os
import telebot
import json
import requests
import time
from multiprocessing.pool import ThreadPool

from functools import wraps
from pydub import AudioSegment
import re

from telegram import ChatAction

from language_functions import phrase_on_language
from config_api import API_TOKEN


bot = telebot.TeleBot(API_TOKEN)


def create_users_data_dir(message):
    user_chat_id = str(message.chat.id)
    # mkdir for special user
    path = "users_data/{}".format(user_chat_id)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed or this directory exists" % path)
    else:
        print("Successfully created the directory %s " % path)

    # trying to change directory and download a video to user's dir
    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
    string = '{"language": "' + 'uk' + '"}'
    user_data = json.loads(string)
    with open(full_file_path + "_data" + ".json", "w") as f:
        json.dump(user_data, f)


def create_user_answers(message, answer):
    try:
        user_chat_id = str(message.chat.id)
    except:
        user_chat_id = str(message.from_user.id)

    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
    with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
        file_user_data = json.load(f)
        file_user_data['survey_answers'] = file_user_data.get('survey_answers', [])
        file_user_data['survey_answers'].append(answer)

    with open(full_file_path + "_data" + ".json", "w", encoding='utf-8') as f:
        json.dump(file_user_data, f, ensure_ascii=False)


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(message, *args, **kwargs):
        bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        return func(message,  *args, **kwargs)

    return command_func


def delete_video(message):
    user_chat_id = str(message.chat.id)
    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id)

    # If the file exists, delete it
    try:
        os.remove(os.path.join(full_file_path, user_chat_id + 'downloaded_video_{}.mp4'.format(user_chat_id)))
    except:
        print('downloaded_video does not exist')


def improve_and_upload_buttons(message):
    """
    :return: a button to improve video or upload a new video
    """
    try:
        language_phrase = phrase_on_language(message, "improve_and_upload_buttons")
    except:
        create_users_data_dir(message)
        language_phrase = phrase_on_language(message, "improve_and_upload_buttons")

    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.row(
        telebot.types.InlineKeyboardButton('📚 ' + language_phrase[0], callback_data='improve')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('📋 ' + language_phrase[3], callback_data='change_music_params')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('🔄 ' + language_phrase[2], callback_data='upload_video2')
    )
    bot.send_message(message.chat.id, language_phrase[1],
                     reply_markup=keyboard, disable_notification=True)


def download_url(url):
    # assumes that the last segment after the / represents the file name
    # if url is abc/xyz/file.txt, the file name will be file.txt
    url_end = url.rfind("|")
    url_for_download = url[:url_end]
    file_name = url[url_end + 1:]

    try:
        r = requests.get(url_for_download, stream=True)
        if r.status_code == requests.codes.ok:
            with open(file_name, 'wb') as f:
                for data in r:
                    f.write(data)

    except:
        print('download_url error - r = requests.get(url_for_download, stream=True)')

    return url


def send_other_musics(message):
    """
    :return: 4 songs with 60 sec duration - other top 4 special for this video
    """
    try:
        language_phrases = phrase_on_language(message, "send_video_to_user")

    except:
        create_users_data_dir(message)
        language_phrases = phrase_on_language(message, "send_video_to_user")

    user_chat_id = str(message.chat.id)
    error_phrases = phrase_on_language(message, 'send_video_to_user')

    full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
    try:
        with open(full_file_path + 'musics5_for_video' + ".json", 'r') as musics5_file:
            musics5 = json.load(musics5_file)

    except:
        bot.send_message(message.chat.id, language_phrases[3])

    audios_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, 'musics_for_video')
    try:
        os.mkdir(audios_path)
    except OSError:
        print("Creation of the directory %s failed or this directory exists" % audios_path)
    else:
        print("Successfully created the directory %s " % audios_path)

    audio_names = []
    # if dir is empty - save
    urls = []
    titles = []
    n_selected_music = ''
    
    audio_names_for_sending = []
    bot.send_message(message.chat.id, language_phrases[5])
    bot.send_chat_action(message.chat.id, 'upload_audio')
    
    try:
        for i in range(len(musics5["extra_music"])):
            url = musics5["extra_music"][i]["download-link"]
            title = musics5["extra_music"][i]["title"]
            title = re.sub(r"[#%!@*']", "", title)
            title = re.findall(r"[\w']+", title)
            title = '_'.join(title)
            titles.append(title)
            audio_name = os.path.join(audios_path, title + '.mp3')
            audio_names.append(audio_name)
            if not title + '.mp3' in os.listdir(audios_path):
                url += '|' + audio_name
                urls.append(url)
    except:
        print('send_other_musics error -  range(len(musics5["extra_music"]))')
        bot.send_message(message.chat.id, error_phrases[4])
    
    try:
        if urls:
            # Run several multiple threads. Each call will take the next element in urls list
            pool = ThreadPool(len(urls))
            results = pool.map(download_url, urls)
            pool.close()
            pool.join()

            audio_names_for_sending = []
            for i in range(len(musics5["extra_music"])):
                audio_name = audio_names[i]
                song = AudioSegment.from_mp3(audio_name)

                # if the audio is longer then 60 sec - cut it to 60 sec
                len_s = len(song)
                if len_s > 60 * 1000:
                    new_audio_name = os.path.join(audios_path, titles[i] + '_trim' + '.mp3')
                    thirty_seconds = 30 * 1000
                    mid = len(song) // 2

                    middle_seconds_song = song[mid - thirty_seconds: mid + thirty_seconds]
                    middle_seconds_song.export(new_audio_name, format='mp3')
                    audio_name, new_audio_name = new_audio_name, audio_name

                audio_names_for_sending.append(audio_name)
                n_selected_music = musics5["selected_music"]

        else:
            user_chat_id = str(message.chat.id)
            full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)

            n_selected_music = 0
            try:
                with open(full_file_path + ".json", "r") as f:
                    data = json.loads(f.read())

                n_selected_music = data["selected_music"]
                for i in range(len(musics5["extra_music"])):
                    title = musics5["extra_music"][i]["title"]
                    title = re.sub(r"[#%!@*']", "", title)
                    title = re.findall(r"[\w']+", title)
                    title = '_'.join(title)
                    audio_name = os.path.join(audios_path, title + '_trim' + '.mp3')
                    audio_names_for_sending.append(audio_name)

            except:
                print('send_other_musics error - data = json.loads(f.read())')
                bot.send_message(message.chat.id, error_phrases[4])

    except:
        print('send_other_musics error -  range(len(musics5["extra_music"])) '
              'or  pool = '
              'ThreadPool(len(musics5["extra_music"]))')
        bot.send_message(message.chat.id, error_phrases[4])

    if n_selected_music != '':
        full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
        try:
            with open(full_file_path + "_data" + ".json", "r", encoding='utf-8') as f:
                file_user_data = json.load(f)
                file_user_data["n_selected_music"] = n_selected_music
                file_user_data["audio_names"] = audio_names_for_sending

            with open(full_file_path + "_data" + ".json", "w") as f:
                json.dump(file_user_data, f)
        except:
            print('send_other_musics error - file_user_data["n_selected_music"] = n_selected_music')
            bot.send_message(message.chat.id, error_phrases[4])

        try:
            language_phrases = phrase_on_language(message, "send_other_musics")

        except:
            create_users_data_dir(message)
            language_phrases = phrase_on_language(message, "send_other_musics")

        audios = []
        for audio_name in audio_names_for_sending:
            try:
                try:
                    audio = open(audio_name, 'rb')
                except:
                    pos = audio_name.find('.')
                    audio_name = audio_name[:pos - 5] + audio_name[pos:]
                    audio = open(audio_name, 'rb')
                audios.append(audio)

            except:
                print('send_other_musics error - audio = open(audio_name')
                bot.send_message(message.chat.id, error_phrases[4])

        n_on_button_audios = [0 for i in range(5)]
        n_audio = 1
        for i in range(len(n_on_button_audios)):
            if i == n_selected_music:
                n_on_button_audios[i] = 0

            else:
                n_on_button_audios[i] = n_audio
                n_audio += 1

        try:
            for i in range(len(musics5["extra_music"])):
                if n_on_button_audios[i] != 0:
                    if i == 0:
                        bot.send_audio(message.chat.id, audios[i])

                    else:
                        bot.send_audio(message.chat.id, audios[i], disable_notification=True)

        except:
            pass
        length_cycle = len(audios)

        keyboard = telebot.types.InlineKeyboardMarkup()

        n_audio_buttons = []
        for i in range(length_cycle):
            if n_on_button_audios[i] != 0:
                callback_button = telebot.types.InlineKeyboardButton(text=str(n_on_button_audios[i]),
                                                                     callback_data='audio_' + str(i))
                n_audio_buttons.append(callback_button)

        keyboard.add(*n_audio_buttons)
        bot.send_message(message.chat.id, language_phrases[1],
                         reply_markup=keyboard)

        for audio in audios:
            audio.close()

    else:
        bot.send_message(message.chat.id, error_phrases[4])
