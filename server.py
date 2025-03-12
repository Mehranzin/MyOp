from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
app.secret_key = 'chave_secreta'

DATABASE_PATH = "users.db"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Retorna os resultados como dicionários
    return conn

# Inicializa o banco de dados
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    idade INTEGER,
                    sexualidade TEXT CHECK(sexualidade IN ('Homem', 'Mulher', 'Outro')),
                    email TEXT UNIQUE,
                    senha TEXT,
                    foto TEXT
                )''')
    conn.commit()
    conn.close()
init_db()

# Verifica se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        sexualidade = request.form['sexualidade']
        email = request.form['email']
        senha = request.form['senha']
        
        foto = request.files.get('foto')
        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(foto_path)
        else:
            foto_path = 'static/uploads/default.jpg'

        senha_hash = generate_password_hash(senha)
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (nome, idade, sexualidade, email, senha, foto) VALUES (?, ?, ?, ?, ?, ?)",
                      (nome, idade, sexualidade, email, senha_hash, foto_path))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email já cadastrado!"
        finally:
            conn.close()
    return render_template('register.html')

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

        if user and check_password_hash(user['senha'], senha):
            session['user'] = dict(user)
            return redirect(url_for('index'))
        else:
            return "Falha no Login! Verifique os dados."
    return render_template('login.html')

@app.route('/perfil')
def perfil():
    if 'user' in session:
        return render_template('perfil.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    
    # Verifica se a pasta de uploads existe, se não, cria
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

foto.save(foto_path)
