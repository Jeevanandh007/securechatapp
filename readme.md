Created the basic chat application using flask tutorial:  https://thepythoncode.com/article/how-to-build-a-chat-app-in-python-using-flask-and-flasksocketio

# Secure Chat Application

This is a secure chat application built using Flask and Flask-SocketIO. The app provides secure communication between users with AES encryption, Google authentication, and client-side encryption/decryption, RSA Digital Signature. 

## Features
- **Real-time Messaging**: Chat with others in real-time by creating or joining chat rooms.
- **Google OAuth 2.0 Authentication**: Securely log in using your Google account.
- **AES Secure message encryption.
- **Client-Side Encryption/Decryption**: Messages are encrypted on the client side before being sent and decrypted after receipt.
- **Digital Signature**: Implemented digital signature for message authenticity using RSA key pairs.


##References:
**RSA key pair generation:https://cryptography.io/en/latest/
**https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/

**Google auth:https://medium.com/@miracyuzakli/user-login-and-registration-with-flask-and-google-oauth-2-0-6f5aee1b64ad

**Client side encryption and decryption:
**https://cryptojs.gitbook.io/docs

**Digital signature:
**https://stackoverflow.com/questions/68159667/save-json-in-local-storage-after-the-fetch
**https://kjur.github.io/jsrsasign/api/symbols/KJUR.crypto.Signature.html

**https://docs.google.com/document/d/1HMN6alJRSpuDhW7HAKvMbDSnfr2jdN3IAPV0CwQ2aq8/edit?usp=sharing

- ##Web URL: https://jeevanandhcloud007.pythonanywhere.com/ DISCONTINUED DUE TO WEBSOCKET ISSUES
- ##New URL: https://jeevandns.francecentral.cloudapp.azure.com/


##How to use the web app: 
- **Login to the application using google login.
- **Click on create room or join an exisiting room using code shared by the other person.
- **Share room code to receiver of message through any other medium.
- **Type in message and click send button.
