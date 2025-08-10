from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange, Optional
from models import User, db

class RegistrationForm(FlaskForm):
    nome = StringField('Nome', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Length(max=15, message='O nome deve ter no máximo 15 caracteres.')
    ])
    sobrenome = StringField('Sobrenome', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Length(max=15, message='O sobrenome deve ter no máximo 15 caracteres.')
    ])
    apelido = StringField('Apelido/Anônimo', validators=[
        Optional(),
        Length(max=13, message='O apelido deve ter no máximo 13 caracteres.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Email(message='Formato de e-mail inválido.'),
        Length(max=120, message='O e-mail deve ter no máximo 120 caracteres.')
    ])
    idade = IntegerField('Idade', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        NumberRange(min=10, max=90, message='Você deve ter entre 10 a 90 anos')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Length(min=6, message='A senha deve ter no mínimo 6 caracteres.')
    ])
    password2 = PasswordField('Repita a senha', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        EqualTo('password', message='As senhas não estão iguais.')
    ])
    submit = SubmitField('Registrar')

    def validate_email(self, email):
        user = User.query.filter(db.func.lower(User.email) == email.data.lower()).first()
        if user:
            raise ValidationError('Email já em uso.')

    def validate_apelido(self, apelido):
        if apelido.data:
            user = User.query.filter_by(apelido=apelido.data).first()
            if user:
                raise ValidationError('Apelido já em uso.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Email(message='Formato de e-mail inválido.')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Este campo é obrigatório.')
    ])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class PostForm(FlaskForm):
    body = TextAreaField('O que está pensando?', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Length(max=280, message='O post deve ter no máximo 280 caracteres.')
    ])
    submit = SubmitField('Publicar')

class CommentForm(FlaskForm):
    body = TextAreaField('Comentário', validators=[
        DataRequired(message='Este campo é obrigatório.'),
        Length(max=280, message='O comentário deve ter no máximo 280 caracteres.')
    ])
    submit = SubmitField('Comentar')