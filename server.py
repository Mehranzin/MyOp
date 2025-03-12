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

# Inicializar o banco de dados
def init_db():
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

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        idade = request.form['idade']
        nacionalidade = request.form['nacionalidade']
        genero = request.form['genero']
        senha = request.form['senha']
        data_criacao = datetime.now().strftime('%Y-%m-%d')  # Somente a data

        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                filename = secure_filename(foto.filename)
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(foto_path)
            else:
                filename = 'default.jpg'
        else:
            filename = 'default.jpg'

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (nome, email, idade, nacionalidade, genero, senha, foto, data_criacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (nome, email, idade, nacionalidade, genero, senha, filename, data_criacao))
            conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

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

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, foto FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('index.html', user=user)

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, idade, nacionalidade, genero, foto, data_criacao FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
    return render_template('perfil.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
