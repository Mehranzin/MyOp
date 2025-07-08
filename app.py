from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Post
from datetime import datetime, timezone
import random
import string
from config import Config
from flask import request
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)

app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.permanent_session_lifetime = timedelta(days=30)

db.init_app(app)

with app.app_context():
    db.create_all()

def gera_apelido():
    for i in range(1, 1001):
        apelido = f"Any{str(i).zfill(3)}"
        if not User.query.filter_by(apelido=apelido).first():
            return apelido
    return None

def tempo_relativo(post_time):
    agora = datetime.now(timezone.utc)
    diff = agora - post_time

    segundos = diff.total_seconds()
    minutos = segundos // 60
    horas = minutos // 60
    dias = diff.days

    if segundos < 60:
        return f"Postado há {int(segundos)}s"
    if minutos < 60:
        return f"Postado há {int(minutos)}min"
    if horas < 24:
        return f"Postado há {int(horas)}h"
    if dias < 7:
        return f"Postado há {int(dias)} dia{'s' if dias > 1 else ''}"
    return f"Postado em {post_time.strftime('%d/%m/%Y')}"

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        return redirect(url_for('feed'))
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():

    if session.get('user_id'):
        flash('Você já está logado e não pode se registrar novamente.', 'info')
        return redirect(url_for('feed'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        sobrenome = request.form.get('sobrenome')
        email = request.form.get('email')
        idade = request.form.get('idade')
        senha = request.form.get('senha')
        confirma_senha = request.form.get('confirma_senha')
        apelido = request.form.get('apelido')

        if not (nome and sobrenome and email and idade and senha and confirma_senha):
            flash('Preencha todos os campos obrigatórios', 'warning')
            return redirect(url_for('register'))

        if senha != confirma_senha:
            flash('Senha e confirmação não conferem', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('register'))

        if apelido:
            if User.query.filter_by(apelido=apelido).first():
                flash('Apelido já em uso', 'warning'
                return redirect(url_for('register'))
        else:
            apelido = gera_apelido()
            if not apelido:
                flash('Limite de apelidos esgotado', 'danger')
                return redirect(url_for('register'))

        try:
            idade_int = int(idade)
        except:
            flash('Idade inválida', 'danger')
            return redirect(url_for('register'))

        novo = User(nome=nome, sobrenome=sobrenome, email=email, idade=idade_int, apelido=apelido)
        novo.set_senha(senha)

        db.session.add(novo)
        db.session.commit()

        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if session.get('user_id'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('feed'))

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        usuario = User.query.filter_by(email=email).first()
        if usuario and usuario.checa_senha(senha):
            session.permanent = True
            session['user_id'] = usuario.id
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('feed'))
        else:
            flash('Email ou senha inválidos', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/perfil')
def perfil():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    apelido_param = request.args.get('usuario')
    if apelido_param:
        usuario = User.query.filter_by(apelido=apelido_param).first()
        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('feed'))
    else:
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
            flash('Postagem criada com sucesso!', 'success')
            return redirect(url_for('feed'))
        else:
            flash('Escreva algo para postar.', 'warning')

    posts = Post.query.order_by(Post.id.desc()).all()
    posts_com_tempo = [(post, tempo_relativo(post.created_at)) for post in posts]

    return render_template('feed.html', posts=posts_com_tempo, apelido=usuario.apelido)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)