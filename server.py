from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Cria o banco de dados e a tabela
def init_db():
    with sqlite3.connect("chat.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                text TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send_message():
    user = request.form["user"]
    text = request.form["text"]

    with sqlite3.connect("chat.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (user, text) VALUES (?, ?)", (user, text))
        conn.commit()

    return jsonify({"status": "success"})

@app.route("/messages")
def get_messages():
    with sqlite3.connect("chat.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user, text FROM messages ORDER BY id DESC")
        messages = cursor.fetchall()

    return jsonify(messages)

# 🚀 Inicia o servidor Flask na porta correta para o Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Usa a variável de ambiente do Render
    app.run(host="0.0.0.0", port=port, debug=True)
    
from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Aqui você pode adicionar a validação do usuário
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# Rota para a página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Aqui você pode adicionar a lógica de registro (armazenar no banco de dados, etc)
        return redirect(url_for('login'))
    return render_template('register.html')

# Página de dashboard (após login)
@app.route('/dashboard')
def dashboard():
    return 'Bem-vindo ao painel de controle!'

if __name__ == '__main__':
    app.run(debug=True)
