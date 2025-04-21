from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat')
def chat():
    agent_id = 'general'
    return render_template('chat.html', agent_id=agent_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)