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
                session['user_key']= record[-2]
                session['username']= username
                session['password']= password

        else:
            if ollama_key:
                key_check=True
                cursor.execute("SELECT * FROM users WHERE user = %s", (username,))

                record = cursor.fetchone()
                if username == record[0]:
                    user_check = True
                if not user_check:
                    cursor.execute("insert into users (user, pass, ollama_api_key, history) values (%s,%s,%s,%s)",(username,password,ollama_key,[]))
                    connection.commit()
                    is_correct=True
                    session['user_key']= ollama_key
                    session['username']= username
                    session['password']= password

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
    username = session.get('username')
    password = session.get('password')
    user_key = session.get('user_key')
    if not username:
        return redirect(url_for('index'))
    cursor.execute("SELECT pass,ollama_api_key FROM users WHERE user = %s", (username,))
    record = cursor.fetchone()
    if record and user_key!=record[-1]:
        session['user_key']=record[-1]
    if 'user_key' not in session or password!=record[0]:
        return redirect(url_for('index'))
    return send_from_directory('.', 'index.html')

@app.route('/')
def index():
    username = session.get('username')
    password = session.get('password')
    cursor.execute("SELECT pass FROM users WHERE user = %s", (username,))
    record = cursor.fetchone()
    if password==record and password!=None:
        return redirect(url_for('home_page'))
    return send_from_directory('.', 'login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/get_account_info', methods=['GET'])
def get_account_info():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    try:
        cursor.execute("SELECT pass, ollama_api_key FROM users WHERE user = %s", (username,))
        record = cursor.fetchone()
        if record:
            return jsonify({
                'success': True,
                'password': record[0],
                'ollama_key': record[1]
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/update_account', methods=['POST'])
def update_account():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    data = request.json
    new_password = data.get('password')
    new_key = data.get('ollama_key')

    if not new_password and not new_key:
        return jsonify({'success': False, 'error': 'No updates provided'}), 400

    try:
        if new_password:
            cursor.execute("UPDATE users SET pass = %s WHERE user = %s", (new_password, username))
            session['password']= new_password

        if new_key:
            cursor.execute("UPDATE users SET ollama_api_key = %s WHERE user = %s", (new_key, username))
            session['user_key'] = new_key

        connection.commit()
        return jsonify({'success': True, 'message': 'Account updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    


@app.route('/chat', methods=['POST'])
def chat():
    username = session.get('username')
    user_key = session.get('user_key')
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
        history.insert(0, {"role": "system", "content": "You are a student counselor answer questions regarding this only and give a little shorter answers"})

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
