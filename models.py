from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    apelido = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(500), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checa_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    autor = db.relationship('User', backref=db.backref('posts', lazy=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
