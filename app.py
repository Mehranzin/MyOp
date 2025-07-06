import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from sqlalchemy import text
from config import Config
from models import db, User, Post, Comment, Like
from forms import RegistrationForm, LoginForm, PostForm, CommentForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post publicado.')
        return redirect(url_for('feed'))

    posts = current_user.followed_posts().all() + current_user.posts.order_by(Post.timestamp.desc()).all()
    posts = sorted(posts, key=lambda p: p.timestamp, reverse=True)

    comment_forms = {post.id: CommentForm(prefix=str(post.id)) for post in posts}
    
    for post in posts:
        post.comments_ordered = post.comments.order_by(text('timestamp desc')).all()

    return render_template('feed.html', posts=posts, form=form, comment_forms=comment_forms)

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm(prefix=str(post_id))
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Comentário publicado.')
    else:
        flash('Erro no comentário.')
    return redirect(url_for('feed'))

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        flash('Like removido.')
    else:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
        flash('Like adicionado.')
    return redirect(url_for('feed'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            apelido=form.apelido.data,
            email=form.email.data,
            idade=form.idade.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso. Agora faça login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email ou senha inválidos.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('feed')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu.')
    return redirect(url_for('login'))

@app.route('/perfil/<apelido>')
@login_required
def perfil(apelido):
    user = User.query.filter_by(apelido=apelido).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('perfil.html', user=user, posts=posts)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash('Post atualizado.')
        return redirect(url_for('feed'))
    elif request.method == 'GET':
        form.body.data = post.body
    return render_template('edit_post.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
