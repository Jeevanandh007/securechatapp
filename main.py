import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from authlib.integrations.flask_client import OAuth
import random
from string import ascii_letters
import secrets

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
socketio = SocketIO(app)

#Authlib setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    authorize_params=None,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    client_kwargs={'scope': 'openid email profile'},
    redirect_uri='http://127.0.0.1:5000/login/authorized',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    issuer='https://accounts.google.com'
)

# A mock database to persist data
rooms = {}

# TODO: Build the routes

def generate_room_code(length: int, existing_codes: list[str]) -> str:
    while True:
        code_chars = [random.choice(ascii_letters) for _ in range(length)]
        code = ''.join(code_chars)
        if code not in existing_codes:
            return code
    
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login():
    nonce = secrets.token_urlsafe()
    session['nonce']=nonce
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/login/authorized')
def authorized():
    token=google.authorize_access_token()
    nonce = session.pop('nonce', None)
    user_info = google.parse_id_token(token, nonce=nonce)
    session['user_email'] = user_info['email']
    return redirect(url_for('homr'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/home', methods=["GET", "POST"])
def home():
    if 'user_email' not in session:
        return redirect(url_for('index'))
    
    email = session.get('user_email')

    if request.method == "POST":
        create = request.form.get('create', False)
        code = request.form.get('code')
        join = request.form.get('join', False)
        if create != False:
            room_code = generate_room_code(6, list(rooms.keys()))
            new_room = {
                'members': 0,
                'messages': []
            }
            rooms[room_code] = new_room
        if join != False:
            # no code
            if not code:
                return render_template('home.html', error="Please enter a room code to enter a chat room", name=name)
            # invalid code
            if code not in rooms:
                return render_template('home.html', error="Room code invalid", name=name)
            room_code = code
        session['room'] = room_code
        session['user_email'] = email
        return redirect(url_for('room'))
    else:
        return render_template('home.html', user_email=email)
    
@app.route('/room')
def room():
    room = session.get('room')
    email = session.get('user_email')
    if email is None or room is None or room not in rooms:
        return redirect(url_for('home'))
    messages = rooms[room]['messages']
    return render_template('room.html', room=room, user=email, messages=messages)

# TODO: Build the SocketIO event handlers
...
@socketio.on('connect')
def handle_connect():
    email = session.get('user_email')
    room = session.get('room')
    if email is None or room is None:
        return
    if room not in rooms:
        leave_room(room)
    join_room(room)
    send({
        "sender": "",
        "message": f"{email} has entered the chat"
    }, to=room)
    rooms[room]["members"] += 1
...

...
@socketio.on('message')
def handle_message(payload):
    room = session.get('room')
    email = session.get('user_email')
    if room not in rooms:
        return
    message = {
        "sender": email,
        "message": payload["message"]
    }
    send(message, to=room)
    rooms[room]["messages"].append(message)
...

...
@socketio.on('disconnect')
def handle_disconnect():
    room = session.get("room")
    email = session.get("user_email")
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
        send({
        "message": f"{email} has left the chat",
        "sender": ""
    }, to=room)
...

if __name__ == "__main__":
    socketio.run(app, debug=True)