from flask import Flask, request, render_template, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
socketio = SocketIO(app)

# A mock database to persist data
rooms = {}

# TODO: Build the routes

# TODO: Build the SocketIO event handlers

if __name__ == "__main__":
    socketio.run(app, debug=True)