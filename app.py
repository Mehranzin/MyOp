from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Post
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meudb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretoqualquer'

db.init_app(app)

with app.app_context():
    db.create_all()

def gera_apelido():
    while True:
        apelido = 'Any' + ''.join(random.choices(string.digits, k=3))
        if not User.query.filter_by(apelido=apelido).first():
            return apelido

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form.get('nome')
        sobrenome = request.form.get('sobrenome')
        email = request.form.get('email')
        idade = request.form.get('idade')
        senha = request.form.get('senha')
        confirma_senha = request.form.get('confirma_senha')
        apelido = request.form.get('apelido')

        if not (nome and sobrenome and email and idade and senha and confirma_senha):
            flash('Preencha todos os campos obrigatórios')
            return redirect(url_for('register'))

        if senha != confirma_senha:
            flash('Senha e confirmação não conferem')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado')
            return redirect(url_for('register'))

        if apelido:
            if User.query.filter_by(apelido=apelido).first():
                flash('Apelido já em uso')
                return redirect(url_for('register'))
        else:
            apelido = gera_apelido()

        try:
            idade_int = int(idade)
        except:
            flash('Idade inválida')
            return redirect(url_for('register'))

        novo = User(nome=nome, sobrenome=sobrenome, email=email, idade=idade_int, apelido=apelido)
        novo.set_senha(senha)

        db.session.add(novo)
        db.session.commit()

        flash('Cadastro realizado com sucesso')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        usuario = User.query.filter_by(email=email).first()
        if usuario and usuario.checa_senha(senha):
            session['user_id'] = usuario.id
            return redirect(url_for('perfil'))
        else:
            flash('Email ou senha inválidos')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/perfil')
def perfil():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    usuario = User.query.get(user_id)
    return render_template('perfil.html', apelido=usuario.apelido, idade=usuario.idade)

@app.route('/feed', methods=['GET', 'POST'])
def feed():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    usuario = User.query.get(user_id)

    if request.method == 'POST':
        texto = request.form.get('texto')
        if texto:
            post = Post(texto=texto, user_id=usuario.id)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('feed'))

    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('feed.html', posts=posts, apelido=usuario.apelido)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
