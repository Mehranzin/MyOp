import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'colocaumvaloraquipratestes'

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# CRIA AS TABELAS AUTOMATICAMENTE SE NÃO EXISTIREM
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            nome_real VARCHAR(150) NOT NULL,
            apelido VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            conteudo TEXT NOT NULL,
            data TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    conn.commit()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.nome_real = user_dict['nome_real']
        self.apelido = user_dict['apelido']
        self.email = user_dict['email']
        self.senha_hash = user_dict['senha_hash']

@login_manager.user_loader
def load_user(user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (int(user_id),))
        user = cur.fetchone()
        if user:
            return User(user)
    return None

def gerar_anonimo():
    return f"Any{random.randint(1000,9999)}"

@app.route('/')
@login_required
def feed():
    with conn.cursor() as cur:
        cur.execute("""
            SELECT posts.id, posts.conteudo, posts.data, users.apelido
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.data DESC
        """)
        posts = cur.fetchall()
    return render_template('feed.html', posts=posts, user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome_real = request.form.get('nome_real').strip()
        apelido = request.form.get('apelido').strip()
        email = request.form.get('email').strip()
        senha = request.form.get('senha')
        senha_confirm = request.form.get('senha_confirm')

        if senha != senha_confirm:
            flash("Senhas não conferem.", "error")
            return redirect(url_for('register'))

        if apelido == '':
            apelido = gerar_anonimo()

        senha_hash = generate_password_hash(senha)

        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("Email já cadastrado.", "error")
                return redirect(url_for('register'))

            cur.execute("""
                INSERT INTO users (nome_real, apelido, email, senha_hash)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (nome_real, apelido, email, senha_hash))
            user_id = cur.fetchone()['id']
            conn.commit()

        user = User({'id': user_id, 'nome_real': nome_real, 'apelido': apelido, 'email': email, 'senha_hash': senha_hash})
        login_user(user)
        return redirect(url_for('feed'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        senha = request.form.get('senha')

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()
            if user_data and check_password_hash(user_data['senha_hash'], senha):
                user = User(user_data)
                login_user(user)
                return redirect(url_for('feed'))
            else:
                flash("Login inválido.", "error")
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/postar', methods=['POST'])
@login_required
def postar():
    conteudo = request.form.get('conteudo').strip()
    if conteudo:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO posts (user_id, conteudo, data) VALUES (%s, %s, NOW())", (current_user.id, conteudo))
            conn.commit()
    return redirect(url_for('feed'))

if __name__ == '__main__':
    app.run(debug=True)
