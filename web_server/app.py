import os
import json
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename


from flask import Flask, redirect, url_for, render_template, request


app = Flask(__name__)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'webm', 'mkv', 'flv', 'mov', 'wmv', 'm4v', '3gp', 'ogv', 'ogg', 'vob'}
user_chat_id = ''

# @app.route("/", methods=["GET", "POST"])
# def render_main_page():
#     if request.method == "POST":
#         print(request.form)
#         if request.form.get("video_uploads"):
#             return render_template('thanks_form.html')
#
#         else:
#             error = 'send only video'
#             return render_template('upload_form.html', error=error)
#
#     return render_template('upload_form.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global user_chat_id

    try:
        if request.method == 'POST':
            print(request.files)
            file = request.files['video_uploads']
            if file and allowed_file(file.filename):
                # filename = secure_filename(file.filename)
                pos_url = os.getcwd().rfind("\\")
                url = os.getcwd()[:pos_url]
                full_file_path = os.path.join(url, 'users_data', user_chat_id)
                filename = user_chat_id + ".mp4"
                file.save(os.path.join(full_file_path, filename))
                return redirect('https://t.me/harmix_bot', code=302)

        user_chat_id = request.args.get('user_chat_id')
        print(user_chat_id)


    except:
        print('upload_file error app.py web_server ')
        # return render_template('error.html')
    # full_file_path = os.path.join(os.getcwd(), 'users_data', user_chat_id, user_chat_id)
    # string = '{"language": "' + data + '"}'
    # user_data = json.loads(string)
    # with open(full_file_path + "_data" + ".json", "w") as f:
    #     json.dump(user_data, f)
    #
    # with open(full_file_path + "_data" + ".json", "w") as f:
    #     json.dump(file_user_data, f)

    return render_template('upload_form.html')


if __name__ == '__main__':
    app.run(debug=True)

