from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'chave_secreta'  # Chave para sessão

# Criar banco de dados e tabela de usuários se não existir
if not os.path.exists("users.db"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    idade INTEGER,
                    sexualidade TEXT CHECK(sexualidade IN ('Homem', 'Mulher', 'Outro')),
                    email TEXT UNIQUE,
                    senha TEXT
                )''')
    conn.commit()
    conn.close()

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        sexualidade = request.form['sexualidade']
        email = request.form['email']
        senha = request.form['senha']

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (nome, idade, sexualidade, email, senha) VALUES (?, ?, ?, ?, ?)",
                      (nome, idade, sexualidade, email, senha))
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

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND senha = ?", (email, senha))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = user[1]  # Nome do usuário na sessão
            return redirect(url_for('index'))
        else:
            return "Login falhou! Verifique seus dados."

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
