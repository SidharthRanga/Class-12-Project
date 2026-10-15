from flask import Flask, send_from_directory, request, jsonify, session, redirect, url_for
import mysql.connector
from ollama import Client

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="<YOUR_MYSQL_PASSWORD>",
    database="<YOUR_DATABASE_NAME>"
)

cursor = connection.cursor()

app = Flask(__name__)
app.secret_key = 'top-secret'

current_user_key = None

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
    if password:
        pass_check=True
        if mode =="login":
            cursor.execute("SELECT * FROM <TABLE_NAME> WHERE <FIRST_COLUMN_NAME> = %s AND <SECOND_COLUMN_NAME> = %s", (username, password))
            record = cursor.fetchone()
            if record:
                is_correct = True
                session['user_key'] = record[-1]

        else:
            if ollama_key:
                key_check=True
                cursor.execute("SELECT * FROM <TABLE_NAME> WHERE <FIRST_COLUMN_NAME> = %s", (username,))

                record = cursor.fetchone()
                if username == record[0]:
                    user_check = True
                if not user_check:
                    cursor.execute("insert into <TABLE_NAME> (<FIRST_COLUMN_NAME>, <SECOND_COLUMN_NAME>, <THIRD_COLUMN_NAME>) values (%s,%s,%s)",(username,password,ollama_key))
                    connection.commit()
                    is_correct=True
                    session['user_key']=ollama_key

    if is_correct:
        return jsonify({'success': True})
    elif not is_correct and not key_check and mode == "register":
        return jsonify({'success': False, 'error': "Please Enter Your Ollama API Key"})
    elif not is_correct and user_check and mode == "register":
        return jsonify({'success': False, 'error': "This username is taken, Please enter a different one"})
    elif not is_correct and not pass_check:
        return jsonify({'success': False, 'error': "Please Enter Your Password"})
    else:
        return jsonify({'success': False, 'error': 'Invalid Username or Password'})

@app.route('/home')
def home_page():
    if 'user_key' not in session:
        return redirect(url_for('index'))
    return send_from_directory('.', 'index.html')

@app.route('/clear', methods=['POST'])
def clear_history():
    session.pop('chat_history', None)
    return jsonify({'success': True, 'message': 'History cleared!'})

@app.route('/')
def index():
    if 'user_key' in session:
        return redirect(url_for('home_page'))
    return send_from_directory('.', 'login.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_key = session.get('user_key')

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {user_key}"}
    )

    history = session.get('chat_history', [
        {"role": "system", "content": "You are a student counselor answer questions regarding this only"}
    ])

    history.append({"role": "user", "content": user_message})

    try:
        response = client.chat(model="gemma4:31b-cloud", messages=history)
        ai_response = response.message.content
        history.append({"role": "assistant", "content": ai_response})
        session['chat_history'] = history

        return jsonify({'response': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
