from flask import Flask, send_from_directory, request, jsonify, session, redirect, url_for
import mysql.connector
from ollama import Client
import json

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="Project"
)

cursor = connection.cursor()

app = Flask(__name__)
app.secret_key = 'top-secret'


@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.json
    mode = data.get('mode')
    username = data.get('username')
    password = data.get('password')
    ollama_key = data.get('ollama_key')
    session['username']= username
    session['password']= password

    is_correct = False
    user_check=False
    pass_check=False
    key_check = False
    if password:
        pass_check=True
        if mode =="login":
            cursor.execute("SELECT * FROM users WHERE user = %s AND pass = %s", (username, password))
            record = cursor.fetchone()
            if record:
                is_correct = True
                session['user_key'] = record[-2]

        else:
            if ollama_key:
                key_check=True
                cursor.execute("SELECT * FROM users WHERE user = %s", (username,))

                record = cursor.fetchone()
                if username == record[0]:
                    user_check = True
                if not user_check:
                    cursor.execute("insert into users (user, pass, ollama_api_key) values (%s,%s,%s)",(username,password,ollama_key))
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
    username = session.get('username')

    if not username:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    try:
        cursor.execute("UPDATE users SET history = %s WHERE user = %s", (json.dumps([]), username))
        connection.commit()

        return jsonify({'success': True, 'message': 'History cleared from database!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/')
def index():
    if 'user_key' in session:
        return redirect(url_for('home_page'))
    return send_from_directory('.', 'login.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_key = session.get('user_key')
    username = session.get('username')

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {user_key}"}
    )
    cursor.execute("select history from users where user = %s", (username,))
    result = cursor.fetchone()
    if result and result[0]:
        try:
            history = json.loads(result[0])
        except:
            history = []
    else:
        history = []

    if not history or history[0].get('role') != 'system':
        history.insert(0, {"role": "system", "content": "You are a student counselor answer questions regarding this only"})

    history.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat(model="gemma4:31b-cloud", messages=history)
        ai_response = response.message.content
        history.append({"role": "assistant", "content": ai_response})
        cursor.execute("UPDATE users SET history = %s WHERE user = %s", (json.dumps(history), username))
        connection.commit()
        return jsonify({'response': ai_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
