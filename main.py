import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send
from authlib.integrations.flask_client import OAuth
import random
from string import ascii_letters
import secrets
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

class User(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(120), unique=True, nullable=False)
    public_key= db.Column(db.Text, nullable=False)
    created_at= db.Column(db.DateTime(timezone=True), server_default=func.now())

with app.app_context():
    db.create_all()

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

def generate_room_code(length:int, existing_codes: list[str]) -> str:
    while True:
        code_chars = [random.choice(ascii_letters) for _ in range(length)]
        code = ''.join(code_chars)
        if code not in existing_codes:
            return code

def generate_key_pair():
    private_key= rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
        )
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
        )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    
    return private_pem.decode('utf-8'),public_pem.decode('utf-8')


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
    user_email= user_info['email']
    
    user = User.query.filter_by(email=user_email).first()
    if user is None:
    #generate key pair for new user
        private_key,public_key = generate_key_pair()
        new_user = User(email=user_email,public_key=public_key)
        db.session.add(new_user)
        db.session.commit()
    else:
        #exisiting user,generate new key pair private key will be only available for user
        private_key, public_key = generate_key_pair()
        user.public_key = public_key
        db.session.commit()

    session['user_email'] = user_email
    session['public_key'] = public_key
    session['private_key'] = private_key

    return redirect(url_for('home'))



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
                'messages': [],
                'public_keys':{}
            }
            rooms[room_code] = new_room
        if join != False:
            # no code
            if not code:
                return render_template('home.html', error="Please enter a room code to enter a chat room", user_email=email)
            # invalid code
            if code not in rooms:
                return render_template('home.html', error="Room code invalid", user_email=email)
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
    
    user =User.query.filter_by(email=email).first()
    if user:
         rooms[room]['public_keys'][email] = user.public_key

    messages = rooms[room]['messages']
    return render_template('room.html', room=room, user=email, messages=messages, public_keys=rooms[room]['public_keys'])

@app.route('/get_keys')
def get_private_key():
    if 'private_key' not in session or not session['private_key']:
        # Generate a new key pair if one isn't available
        private_key, public_key = generate_key_pair()
        user = User.query.filter_by(email=session['user_email']).first()
        if user:
            user.public_key = public_key
            db.session.commit()
        session['public_key'] = public_key
        session['private_key'] = private_key
        
    private_key = session['private_key']
    public_key = session['public_key']
    session['private_key'] = None #remove privatekey
    return jsonify({
        'private_key': private_key,
        'public_key': public_key
    })



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
    
    user = User.query.filter_by(email=email).first()
    if user:
        message = payload["message"]
        signature = payload.get("signature", "")


    message = {
        "sender": email,
        "message": payload["message"],
        "signature":signature,
        "publicKey": user.public_key
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