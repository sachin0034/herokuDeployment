from flask import Flask
from main import handle_incoming_call, transcribe_message

app = Flask(__name__)

@app.route('/incoming', methods=['POST'])
def incoming_call():
    return handle_incoming_call(request)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    return transcribe_message(request)

if __name__ == '__main__':
    app.run()