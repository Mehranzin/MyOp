from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import RegisterForm, LoginForm, PostForm, CommentForm
from models import db, User, Post, Comment, Like
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dacertoDeus'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://your_connection_string'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods=["GET", "POST"])
@login_required
def feed():
    form = PostForm()
    comment_form = CommentForm()
    if form.validate_on_submit():
        post = Post(content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("feed"))
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("feed.html", form=form, posts=posts, user=current_user, comment_form=comment_form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nickname = form.nickname.data or f"Any{random.randint(1,1000):03}"
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            age=form.age.data,
            nickname=nickname
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("feed"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("feed"))
        flash("Login inválido")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, user_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for("feed"))

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    if not Like.query.filter_by(user_id=current_user.id, post_id=post_id).first():
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
    return redirect(url_for("feed"))
