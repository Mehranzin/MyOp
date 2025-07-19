from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from models import User
from wtforms.validators import Optional

class RegistrationForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=64)])
    sobrenome = StringField('Sobrenome', validators=[DataRequired(), Length(max=64)])
    apelido = StringField('Apelido/Anônimo', validators=[Optional(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    idade = IntegerField('Idade', validators=[DataRequired(), NumberRange(min=10, max=90)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repita a senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email já está em uso.')

    def validate_apelido(self, apelido):
        if apelido.data:
            user = User.query.filter_by(apelido=apelido.data).first()
        if user:
            raise ValidationError('Apelido já está em uso.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class PostForm(FlaskForm):
    body = TextAreaField('O que está pensando?', validators=[DataRequired(), Length(max=280)])
    submit = SubmitField('Publicar')

class CommentForm(FlaskForm):
    body = TextAreaField('Comentário', validators=[DataRequired(), Length(max=280)])
    submit = SubmitField('Comentar')
