from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名是唯一标识,必须是字母或者数字.')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='两次密码不相同!')])
    password2 = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('这个邮件已经被注册过了!')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('这个用户名已经被使用过了!')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators = [DataRequired()])
    new_password = PasswordField('新密码', validators = [DataRequired(), EqualTo('new_password2', message = '两次密码不相同')])
    new_password2 = PasswordField('重复新密码', validators = [DataRequired()])
    submit = SubmitField('修改密码')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('邮箱', validators = [DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('发送重置密码邮件')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators = [DataRequired(), EqualTo('password2', message = '两次密码不相同')])
    password2 = PasswordField('重复新密码', validators = [DataRequired()])
    submit = SubmitField('重置密码')

class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators = [DataRequired(), Length(1, 64), Email()])
    password = PasswordField('当前账户密码', validators = [DataRequired()])
    submit = SubmitField('修改账户邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('邮箱已经被注册')
