from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Post, Comment, Like
from datetime import datetime, timezone, timedelta
from config import Config
from sqlalchemy import or_, text, func
from forms import RegistrationForm

app = Flask(__name__)
app.config.from_object(Config)

app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.permanent_session_lifetime = timedelta(days=30)

db.init_app(app)

with app.app_context():
    db.drop_all()
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

@app.route('/api/validar_passo', methods=['POST'])
def validar_passo():
    data = request.json
    form = RegistrationForm(data=data, meta={'csrf': False})
    form.validate()
    
    erros_do_passo = {}
    passo = data.get('passo')

    if passo == 1:
        campos_do_passo = ['nome', 'sobrenome']
    elif passo == 2:
        campos_do_passo = ['apelido', 'idade']
    elif passo == 3:
        campos_do_passo = ['email', 'password', 'password2']
    else:
        return jsonify({'success': False, 'erros': {'geral': ['Passo de validação inválido.']}}), 400

    for campo_nome in campos_do_passo:
        if campo_nome in form.errors:
            erros_do_passo[campo_nome] = form.errors[campo_nome]

    if 'csrf_token' in erros_do_passo:
        del erros_do_passo['csrf_token']
    
    return jsonify({'success': not erros_do_passo, 'erros': erros_do_passo})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        flash('Já está logado.', 'info')
        return redirect(url_for('feed'))

    form = RegistrationForm()
    if form.validate_on_submit():
        apelido = form.apelido.data.strip() if form.apelido.data else ''
        if not apelido:
            apelido = gera_apelido()
            if not apelido:
                flash('Limite de apelidos esgotado.', 'danger')
                return redirect(url_for('register'))

        novo = User(
            nome=form.nome.data.strip(),
            sobrenome=form.sobrenome.data.strip(),
            email=form.email.data.strip(),
            idade=form.idade.data,
            apelido=apelido,
            bio=None 
        )
        novo.set_senha(form.password.data.strip())

        db.session.add(novo)
        db.session.commit()

        flash('Cadastro feito. Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        flash('Já está logado.', 'info')
        return redirect(url_for('feed'))

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        usuario = User.query.filter(db.func.lower(User.email) == email.lower()).first()
        if usuario and usuario.checa_senha(senha):
            session.permanent = True
            session['user_id'] = usuario.id
            session['user_email'] = usuario.email
            flash('Login bem-sucedido.', 'success')
            return redirect(url_for('feed'))
        flash('Credenciais inválidas.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
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
        posts_do_usuario = Post.query.filter_by(user_id=usuario.id).order_by(Post.id.desc()).all()
        is_owner = (usuario.id == session['user_id'])
    else:
        usuario = User.query.get(session['user_id'])
        posts_do_usuario = Post.query.filter_by(user_id=usuario.id).order_by(Post.id.desc()).all()
        is_owner = True

    posts_com_detalhes = []
    for post in posts_do_usuario:
        tempo = tempo_relativo(post.created_at)
        likes_count = Like.query.filter_by(post_id=post.id).count()
        comentarios_count = Comment.query.filter_by(post_id=post.id).count()
        liked = Like.query.filter_by(post_id=post.id, user_id=session['user_id']).first() is not None
        posts_com_detalhes.append({
            'post': post,
            'tempo': tempo,
            'likes_count': likes_count,
            'comentarios_count': comentarios_count,
            'liked': liked
        })

    return render_template('perfil.html',
                           usuario=usuario,
                           posts=posts_com_detalhes,
                           is_owner=is_owner)


@app.route('/salvar_bio', methods=['POST'])
def salvar_bio():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Usuário não autenticado.'}), 401
    
    user_id = session['user_id']
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404

    bio_nova = request.form.get('bio')
    
    if len(bio_nova) > 255:
        return jsonify({'success': False, 'message': 'A biografia deve ter no máximo 255 caracteres.'}), 400

    usuario.bio = bio_nova.strip()
    db.session.commit()

    flash('Biografia atualizada com sucesso!', 'success')
    return redirect(url_for('settings', bio_salva=True))


@app.route('/feed', methods=['GET', 'POST'])
def feed():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    usuario = User.query.get(session['user_id'])
    if not usuario:
        session.clear()
        flash('Sua sessão expirou. Faça login novamente.', 'warning')
        return redirect(url_for('login'))

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
    return redirect(request.referrer or url_for('feed'))

@app.route('/api/like/<int:post_id>', methods=['POST'])
def like_post_api(post_id):
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Usuário não autenticado.'}), 401

    user_id = session['user_id']
    like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    
    if like:
        db.session.delete(like)
        liked_status = False
    else:
        novo_like = Like(post_id=post_id, user_id=user_id)
        db.session.add(novo_like)
        liked_status = True
    
    db.session.commit()
    
    likes_count = Like.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'status': 'success',
        'liked': liked_status,
        'likes_count': likes_count
    })
@app.route('/comment/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    texto = request.form.get('comentario')
    if texto:
        comentario = Comment(texto=texto, post_id=post_id, user_id=session['user_id'])
        db.session.add(comentario)
        db.session.commit()
    return redirect(request.referrer or url_for('feed'))

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
    if not session.get('user_id'):
        return redirect(url_for('login'))

    usuario = User.query.get(session['user_id'])

    posts_data = (
        db.session.query(
            Post,
            db.func.count(db.distinct(Like.id)).label('likes_count'),
            db.func.count(db.distinct(Comment.id)).label('comentarios_count')
        )
        .outerjoin(Like, Post.id == Like.post_id)
        .outerjoin(Comment, Post.id == Comment.post_id)
        .group_by(Post.id)
        .all()
    )

    posts_com_score = []
    for post, likes_count, comentarios_count in posts_data:
        engagement_score = likes_count + comentarios_count
        posts_com_score.append({
            'post': post,
            'likes_count': likes_count,
            'comentarios_count': comentarios_count,
            'engagement_score': engagement_score
        })

    posts_com_score.sort(key=lambda x: x['engagement_score'], reverse=True)

    posts_para_template = []
    for i, item in enumerate(posts_com_score):
        tempo = tempo_relativo(item['post'].created_at)
        liked = Like.query.filter_by(post_id=item['post'].id, user_id=usuario.id).first() is not None
        
        posts_para_template.append({
            'post': item['post'],
            'tempo': tempo,
            'likes_count': item['likes_count'],
            'comentarios_count': item['comentarios_count'],
            'liked': liked,
            'is_viral': True if i < 3 else False
        })

    return render_template('trending.html', posts=posts_para_template, apelido=usuario.apelido)

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'usuarios': [], 'posts': []})

    unaccented_query = func.unaccent(query.lower())

    usuarios = User.query.filter(
        func.unaccent(func.lower(User.apelido)).ilike(f"%{query.lower()}%")
    ).all()

    posts_texto = Post.query.filter(
        func.unaccent(func.lower(Post.texto)).ilike(f"%{query.lower()}%")
    ).all()

    user_ids = [u.id for u in usuarios]
    posts_usuario = Post.query.filter(Post.user_id.in_(user_ids)).all() if user_ids else []

    posts = {p.id: p for p in posts_texto}
    for p in posts_usuario:
        posts[p.id] = p
    posts = list(posts.values())

    posts_formatados = []
    for p in posts:
        posts_formatados.append({
            'id': p.id,
            'texto': p.texto,
            'autor_apelido': p.autor.apelido,
            'tempo': tempo_relativo(p.created_at)
        })

    return jsonify({
        'usuarios': [{'apelido': u.apelido} for u in usuarios],
        'posts': posts_formatados
    })

@app.route('/groups')
def groups():
    return render_template('groups.html')

@app.route('/admin/uso')
def admin_uso_banco():
    email = session.get('user_email', '').lower()
    if 'user_id' not in session or email != 'mehranmesrob@gmail.com':
        return redirect(url_for('login'))
    
    query = text("""
        SELECT 
            relname AS tabela,
            pg_size_pretty(pg_total_relation_size(relid)) AS tamanho,
            pg_total_relation_size(relid) AS bytes
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC;
    """)
    resultado = db.session.execute(query).fetchall()

    query_total = text("""
        SELECT pg_size_pretty(pg_database_size(current_database())) AS total
    """)
    total = db.session.execute(query_total).scalar()

    return render_template('uso_banco.html', tabelas=resultado, total=total)

@app.route('/api/apelido_disponivel')
def apelido_disponivel():
    apelido = gera_apelido()
    if apelido:
        return jsonify({'apelido': apelido})
    return jsonify({'erro': 'Limite esgotado'}), 400

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    usuario = User.query.get(session['user_id'])

    if request.method == 'POST':
        nova_bio = request.form.get('bio')
        usuario.bio = nova_bio.strip()
        db.session.commit()
        flash('Biografia atualizada com sucesso!', 'success')
        return redirect(url_for('settings'))

    return render_template('perfil_config.html', usuario=usuario)


if __name__ == '__main__':
    app.run(debug=True)