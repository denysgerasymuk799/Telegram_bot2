from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeAudio
import mimetypes

import config_api

entity = 'AudioTube_bot' #имя сессии - все равно какое
api_id = 940913
api_hash = '731a360998a9e83e28fd14cf1334f192'
phone = '+380978683723'
client = TelegramClient(entity, api_id, api_hash)
try:
    await client.connect()
except OSError:
    print('Failed to connect')

if not client.is_user_authorized():
    # client.send_code_request(phone) #при первом запуске - раскомментить, после авторизации для избежания FloodWait советую закомментить
    client.sign_in(phone, input('Enter code: '))
client.start()


def send_to_bot(argv):
    file_path = argv[1]
    file_name = argv[2]
    chat_id = argv[3]
    bot_name = argv[4]
    file_size = argv[5]
    mimetypes.add_type('video/mp4',  '.mp4')
    msg = client.send_file(
                           str(bot_name),
                           file_path,
                           caption=str(chat_id + ':' + file_size),
                           file_name=str(file_name),
                           use_cache=False,
                           part_size_kb=512,
                           attributes=[DocumentAttributeAudio(
                                                      int(file_size),
                                                      voice=None,
                                                      title=file_name[:-4],
                                                      performer='')]
                           )
    client.disconnect()
    return 0


if __name__ == '__main__':
    import sys
    send_to_bot(sys.argv[0:])