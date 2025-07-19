from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Post, Comment, Like
from datetime import datetime, timezone, timedelta
from config import Config
from flask import jsonify
from sqlalchemy import or_

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
        return f"{int(segundos)}s atrás"
    if minutos < 60:
        return f"{int(minutos)}min atrás"
    if horas < 24:
        return f"{int(horas)}h atrás"
    if dias < 7:
        return f"{int(dias)}d atrás"
    return f"{post_time.strftime('%d/%m/%Y')}"

@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        flash('Já está logado.', 'info')
        return redirect(url_for('feed'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        sobrenome = request.form.get('sobrenome', '').strip()
        email = request.form.get('email', '').strip()
        idade = request.form.get('idade', '').strip()
        senha = request.form.get('senha', '').strip()
        confirma_senha = request.form.get('confirma_senha', '').strip()
        apelido = request.form.get('apelido', '').strip()

        # Verificações básicas
        if not (nome and sobrenome and email and idade and senha and confirma_senha):
            flash('Preencha todos os campos.', 'warning')
            return redirect(url_for('register'))

        if '@' not in email or '.' not in email:
            flash('Email inválido.', 'danger')
            return redirect(url_for('register'))

        if not idade.isdigit() or int(idade) < 10:
            flash('Idade inválida.', 'danger')
            return redirect(url_for('register'))

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('register'))

        if senha != confirma_senha:
            flash('Senhas não conferem.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email já usado.', 'danger')
            return redirect(url_for('register'))

        if apelido:
            if len(apelido) < 3:
                flash('Apelido deve ter pelo menos 3 caracteres.', 'danger')
                return redirect(url_for('register'))
            if User.query.filter_by(apelido=apelido).first():
                flash('Apelido já usado.', 'warning')
                return redirect(url_for('register'))
        else:
            apelido = gera_apelido()
            if not apelido:
                flash('Limite de apelidos esgotado.', 'danger')
                return redirect(url_for('register'))

        novo = User(
            nome=nome,
            sobrenome=sobrenome,
            email=email,
            idade=int(idade),
            apelido=apelido
        )
        novo.set_senha(senha)

        db.session.add(novo)
        db.session.commit()

        flash('Cadastro feito. Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        flash('Já está logado.', 'info')
        return redirect(url_for('feed'))

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        usuario = User.query.filter_by(email=email).first()
        if usuario and usuario.checa_senha(senha):
            session.permanent = True
            session['user_id'] = usuario.id
            flash('Login bem-sucedido.', 'success')
            return redirect(url_for('feed'))
        flash('Credenciais inválidas.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Saiu da conta.', 'info')
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    apelido_param = request.args.get('usuario')
    if apelido_param:
        usuario = User.query.filter_by(apelido=apelido_param).first()
        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('feed'))
    else:
        usuario = User.query.get(session['user_id'])

    return render_template('perfil.html', apelido=usuario.apelido, idade=usuario.idade)

@app.route('/feed', methods=['GET', 'POST'])
def feed():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    usuario = User.query.get(session['user_id'])

    if request.method == 'POST':
        texto = request.form.get('texto')
        if texto:
            post = Post(texto=texto, user_id=usuario.id)
            db.session.add(post)
            db.session.commit()
            flash('Postado!', 'success')
            return redirect(url_for('feed'))
        flash('Escreva algo.', 'warning')

    posts = Post.query.order_by(Post.id.desc()).all()
    posts_com_tempo = []
    for post in posts:
        tempo = tempo_relativo(post.created_at)
        likes_count = Like.query.filter_by(post_id=post.id).count()
        comentarios = Comment.query.filter_by(post_id=post.id).order_by(Comment.id.desc()).all()
        comentarios_count = len(comentarios)
        liked = Like.query.filter_by(post_id=post.id, user_id=usuario.id).first() is not None
        posts_com_tempo.append((post, tempo, likes_count, comentarios_count, comentarios, liked))

    return render_template('feed.html', posts=posts_com_tempo, apelido=usuario.apelido)

@app.route('/like/<int:post_id>')
def like_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()

    if like:
        db.session.delete(like)
    else:
        novo_like = Like(post_id=post_id, user_id=user_id)
        db.session.add(novo_like)
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    texto = request.form.get('comentario')
    if texto:
        comentario = Comment(texto=texto, post_id=post_id, user_id=session['user_id'])
        db.session.add(comentario)
        db.session.commit()
    return redirect(url_for('feed'))

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash('Você não pode excluir este post.', 'danger')
        return redirect(url_for('feed'))

    db.session.delete(post)
    db.session.commit()
    flash('Post deletado.', 'info')
    return redirect(url_for('feed'))

@app.route('/edit_post/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    post = Post.query.get_or_404(post_id)
    if post.user_id != session['user_id']:
        flash('Você não pode editar este post.', 'danger')
        return redirect(url_for('feed'))

    novo_texto = request.form.get('novo_texto')
    if novo_texto:
        post.texto = novo_texto
        db.session.commit()
        flash('Post editado.', 'success')
    return redirect(url_for('feed'))

@app.route('/post/<int:post_id>')
def ver_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    usuario = User.query.get(session['user_id'])
    post = Post.query.get_or_404(post_id)
    tempo = tempo_relativo(post.created_at)
    likes_count = Like.query.filter_by(post_id=post.id).count()
    comentarios = Comment.query.filter_by(post_id=post.id).order_by(Comment.id.desc()).all()
    liked = Like.query.filter_by(post_id=post.id, user_id=usuario.id).first() is not None

    return render_template(
        'ver_post.html',
        post=post,
        tempo=tempo,
        likes_count=likes_count,
        comentarios=comentarios,
        liked=liked,
        apelido=usuario.apelido
    )
@app.route('/trending')
def trending():
    return render_template('trending.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'usuarios': [], 'posts': []})

    usuarios = User.query.filter(
        or_(
            User.nome.ilike(f"%{query}%"),
            User.sobrenome.ilike(f"%{query}%"),
            User.apelido.ilike(f"%{query}%")
        )
    ).all()

    posts = Post.query.filter(
        Post.texto.ilike(f"%{query}%")
    ).all()

    return jsonify({
        'usuarios': [
            {
                'apelido': u.apelido
            } for u in usuarios
        ],
        'posts': [
            {
                'id': p.id,
                'texto': p.texto,
                'autor_apelido': p.autor.apelido
            } for p in posts
        ]
    })

@app.route('/groups')
def groups():
    return render_template('groups.html')

if __name__ == '__main__':
    app.run(debug=True)
