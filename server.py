from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static')
app.secret_key = 'chave_secreta'  # Chave para sessão

DATABASE_PATH = "users.db"

def init_db():
    if not os.path.exists(DATABASE_PATH):
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT,
                        idade INTEGER,
                        sexualidade TEXT CHECK(sexualidade IN ('Homem', 'Mulher', 'Outro')),
                        email TEXT UNIQUE,
                        senha TEXT
                    )''')
        conn.commit()
        conn.close()

# Inicializa o banco antes de iniciar o Flask
init_db()

def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

# Adiciona a variável 'user' para ser acessada globalmente
@app.context_processor
def inject_user():
    return dict(user=session.get('user'))

# Rota para servir arquivos estáticos corretamente (não é necessário essa rota personalizada)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        sexualidade = request.form['sexualidade']
        email = request.form['email']
        senha = request.form['senha']

        senha_hash = generate_password_hash(senha)  # Criptografa a senha

        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (nome, idade, sexualidade, email, senha) VALUES (?, ?, ?, ?, ?)",
                      (nome, idade, sexualidade, email, senha_hash))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email já cadastrado!"
        finally:
            conn.close()
    
    return render_template('register.html')

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[5], senha):  # Verifica a senha criptografada
            session['user'] = user[1]  # Nome do usuário na sessão
            return redirect(url_for('index'))
        else:
            return "Falha no Login! Verifique os dados."

    return render_template('login.html')

# Rota protegida (página inicial)
@app.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Configurar para escutar no endereço 0.0.0.0
    app.run(host='0.0.0.0', port=8000, debug=True)
