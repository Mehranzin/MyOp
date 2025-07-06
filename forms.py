from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired()])
    surname = StringField("Sobrenome", validators=[DataRequired()])
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    age = IntegerField("Idade", validators=[DataRequired()])
    nickname = StringField("Apelido (ou deixe em branco)")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Senha", validators=[DataRequired()])

class PostForm(FlaskForm):
    content = TextAreaField("O que você pensa hoje?", validators=[DataRequired()])

class CommentForm(FlaskForm):
    content = TextAreaField("Comentário", validators=[DataRequired()])
