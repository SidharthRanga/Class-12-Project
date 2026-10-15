from flask import Flask, send_from_directory, request, jsonify
import mysql.connector
from ollama import Client

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="Project"
)

cursor = connection.cursor()

app = Flask(__name__)

current_user_key = None

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/auth', methods=['POST'])
def authenticate():
    global current_user_key
    data = request.json
    mode = data.get('mode')
    username = data.get('username')
    password = data.get('password')
    ollama_key = data.get('ollama_key')

    is_correct = False
    user_check=False
    pass_check=False
    key_check = False
    if password != "":
        pass_check=True
        if mode =="login":
            cursor.execute("select * from users")
            records = cursor.fetchall()
            for i in records:
                if username == i[0] and password == i[1]:
                    is_correct = True
                    current_user_key = i[-1]

        else:
            if ollama_key:
                key_check=True
                cursor.execute("select * from users")
                records = cursor.fetchall()
                for i in records:
                    if username == i[0]:
                        user_check = True
                if not user_check:
                    cursor.execute("insert into users (user, pass, ollama_api_key) values (%s,%s,%s)",(username,password,ollama_key))
                    connection.commit()
                    is_correct=True
                    current_user_key=ollama_key

    

    if is_correct:
        return jsonify({'success': True})
    elif not is_correct and not key_check:
        return jsonify({'success': False, 'error': "Please Enter Your Ollama API Key"})
    elif not is_correct and user_check:
        return jsonify({'success': False, 'error': "This username is taken, Please enter a different one"})
    elif not is_correct and not pass_check:
        return jsonify({'success': False, 'error': "Please Enter Your Password"})
    else:
        return jsonify({'success': False, 'error': 'Invalid Username or Password'})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global current_user_key

    if not current_user_key:
        return jsonify({'error': 'Please login first'}), 401

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {current_user_key}"}
    )

    messages = [
        {"role": "system", "content": "You are a student counselor answer questions regarding this only"},
        {"role": "user", "content": user_message}
    ]

    try:
        response = client.chat(model="gemma4:31b-cloud", messages=messages)
        return jsonify({'response': response.message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
