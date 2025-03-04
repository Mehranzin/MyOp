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
