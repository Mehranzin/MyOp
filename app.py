from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secreto'
UPLOAD_FOLDER = 'static/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializar bancos de dados
def init_users_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          nome TEXT,
                          email TEXT UNIQUE,
                          idade INTEGER,
                          nacionalidade TEXT,
                          genero TEXT,
                          senha TEXT,
                          foto TEXT,
                          data_criacao TEXT)''')
        conn.commit()

def init_messages_db():
    with sqlite3.connect('messages.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER,
                          mensagem TEXT,
                          data_postagem TEXT)''')
        conn.commit()

# Página inicial redirecionando para o login se o usuário não estiver autenticado
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        mensagem = request.form['mensagem']
        user_id = session['user_id']
        data_postagem = datetime.now().strftime('%Y-%m-%d %H:%M')

        with sqlite3.connect('messages.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (user_id, mensagem, data_postagem) VALUES (?, ?, ?)",
                           (user_id, mensagem, data_postagem))
            conn.commit()

    mensagens = []
    with sqlite3.connect('messages.db') as msg_conn:
        msg_cursor = msg_conn.cursor()
        msg_cursor.execute("SELECT user_id, mensagem, data_postagem FROM messages ORDER BY data_postagem DESC")
        mensagens_brutas = msg_cursor.fetchall()

    with sqlite3.connect('users.db') as user_conn:
        user_cursor = user_conn.cursor()
        for user_id, mensagem, data_postagem in mensagens_brutas:
            user_cursor.execute("SELECT nome FROM users WHERE id=?", (user_id,))
            user = user_cursor.fetchone()
            nome = user[0] if user else "Desconhecido"
            mensagens.append((mensagem, data_postagem, nome))

    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, foto FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()

    return render_template('index.html', user=user, mensagens=mensagens)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=? AND senha=?", (email, senha))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        idade = request.form['idade']
        nacionalidade = request.form['nacionalidade']
        genero = request.form['genero']
        foto = request.files['foto']
        data_criacao = datetime.now().strftime('%Y-%m-%d %H:%M')

        if foto:
            foto_filename = secure_filename(foto.filename)
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
            foto.save(foto_path)
        else:
            foto_path = None

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (nome, email, senha, idade, nacionalidade, genero, foto, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (nome, email, senha, idade, nacionalidade, genero, foto_path, data_criacao))
            conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, idade, nacionalidade, genero, foto, data_criacao FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('perfil.html', user=user)

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/search')
def search():
    return render_template('search.html')

if __name__ == '__main__':
    init_users_db()
    init_messages_db()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
