from flask import Flask, render_template, request, url_for, redirect, session, flash, jsonify
from pymongo import MongoClient
import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "ABCD"


client = MongoClient('localhost', 27017)  
db_cap = client.cap
users = db_cap.users
messages = db_cap.messages
images = db_cap.images
bot_messages = db_cap.bot_messages

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')


@app.route('/')
def index():
    if 'logged_in' in session and 'email' in session:
        user_messages = list(messages.find({"email": session['email']}))
        return render_template('index.html', messages=user_messages)
    else:
        return render_template('first.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        existing_user = users.find_one({"email": email})

        if existing_user:
            flash("Email already exists")
            return render_template('sign.html')
        else:
            users.insert_one({'name': name, 'email': email, 'password': password})
            flash("회원가입 성공")
            return redirect(url_for('login'))

    return render_template('sign.html')
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(f"Debug: Attempting to login with email: {email}, password: {password}")  # Debug line
        login_user = users.find_one({"email": email})

        if login_user:
            print(f"Debug: Found user in database: {login_user}")  # Debug line
            if login_user["password"] == password:
                session['logged_in'] = True
                session['email'] = email
                print(f"Debug: Successful login for email: {email}")  # Debug line
                return redirect(url_for('index'))
            else:
                print("Debug: Password doesn't match")  # Debug line
                flash("로그인 실패")
                return render_template("login.html")
        else:
            print("Debug: No user found in database with this email")  # Debug line
            flash("로그인 실패")
            return render_template("login.html")
    return render_template("login.html")

def generate_bot_response(message, filename):
    if message and filename:
        return f"멋진 사진이네용 ㅎㅎ"
    elif message:
        return f"지당하신 말씀입니다 ㅎㅎ"
    elif filename:
        return f"믓찐 사진입니다 ㅎㅎ"
    else:
        return "I didn't receive a message or file."

@app.route('/send', methods=['GET', 'POST'])
def send():
    print(f"Debug: Session keys: {session.keys()}")  # Debug line
    print(f"Debug: Request method: {request.method}")  # Debug line

    if 'logged_in' in session and 'email' in session:
        message = request.form.get('message')  # Get 'message' field from form data
        print(f"Debug: Received message: {message}")  # Debug line
        file = request.files.get('file')
        if file and message:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            send_time = datetime.datetime.now().strftime("%I:%M %p")
            update = {
                "$push": {
                    "send_times": send_time,
                    "filename": filename,
                    "messages": message
                }
            }
            query = {"email": session['email']}
            images.update_one(query, update)

            bot_response = generate_bot_response(message, filename)  # Generate the bot response based on user's message and filename
            send_time = datetime.datetime.now().strftime("%I:%M %p")
            bot_update = {"$push": {"bot_response": bot_response, "send_times": send_time}}
            bot_messages.update_one(query, bot_update)

            print(f"Debug: Bot response: {bot_response}")  # Debug line

            return jsonify({'message': message, 'filename': filename, 'send_time': send_time, 'bot_response': bot_response})

        elif file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            send_time = datetime.datetime.now().strftime("%I:%M %p")
            update = {
                "$push": {
                    "send_times": send_time,
                    "filename": filename
                }
            }
            query = {"email": session['email']}
            images.update_one(query, update)

            bot_response = generate_bot_response(None, filename)  # Generate the bot response based on filename
            send_time = datetime.datetime.now().strftime("%I:%M %p")
            bot_update = {"$push": {"bot_response": bot_response, "send_times": send_time}}
            bot_messages.update_one(query, bot_update)

            print(f"Debug: Bot response: {bot_response}")  # Debug line

            return jsonify({'filename': filename, 'send_time': send_time, 'bot_response': bot_response})

        elif message:
            send_time = datetime.datetime.now().strftime("%I:%M %p")
            update = {"$push": {"messages": message, "send_times": send_time}}
            query = {"email": session['email']}
            messages.update_one(query, update)

            bot_response = generate_bot_response(message, None)
            send_time = datetime.datetime.now().strftime("%I:%M %p") 
            bot_update = {"$push": {"bot_response": bot_response, "send_times": send_time}}
            bot_messages.update_one(query, bot_update)

            print(f"Debug: Bot response: {bot_response}")  # Debug line

            return jsonify({'message': message, 'send_time': send_time, 'bot_response': bot_response})



        else:
            print("Debug: No 'message' in data")  # Debug line


    else:
        print("Debug: User not logged in")  # Debug line

    return render_template('first.html')



@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    return render_template('login.html')


if __name__ == "__main__":
    app.run()
