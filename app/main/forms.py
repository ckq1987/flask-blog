from flask import request, make_response, url_for, current_app
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User
import os, random, datetime


class NameForm(FlaskForm):
    name = StringField('你的名字', validators=[DataRequired()])
    submit = SubmitField('保存')

class EditProfileForm(FlaskForm):
    name = StringField('你的名字', validators = [Length(0, 64)])
    location = StringField('地址', validators = [Length(0, 64)])
    about_me = StringField('自我介绍', validators = [Length(0, 1000)])
    submit = SubmitField('保存')

class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators = [DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators = [DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名必须是字母或数字')])
    confirmed = BooleanField('账户已经确认?')
    role = SelectField('权限', coerce = int)
    name = StringField('名字', validators = [Length(0, 64)])
    location = StringField('地址', validators = [Length(0, 64)])
    about_me = StringField('自我介绍', validators = [Length(0, 1000)])
    submit = SubmitField('保存')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email = field.data).first():
            raise ValidationError('邮件已经被注册')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username = field.data).first():
            raise ValidationError('用户名已经被使用')

class CKEditor(object):
    def __init__(self):
        pass

    def gen_rnd_filename(self):
        """generate a random filename"""
        filename_prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "%s%s" % (filename_prefix, str(random.randrange(1000, 10000)))

    def upload(self, endpoint=current_app):
        """img or file upload methods"""
        error = ''
        url = ''
        callback = request.args.get("CKEditorFuncNum")

        if request.method == 'POST' and 'upload' in request.files:
            # /static/upload
            fileobj = request.files['upload']
            fname, fext = os.path.splitext(fileobj.filename)
            rnd_name = '%s%s' % (self.gen_rnd_filename(), fext)

            filepath = os.path.join(endpoint.static_folder, 'upload', rnd_name)

            dirname = os.path.dirname(filepath)
            if not os.path.exists(dirname):
                try:
                    os.makedirs(dirname)
                except:
                    error = 'ERROR_CREATE_DIR'
            elif not os.access(dirname, os.W_OK):
                    error = 'ERROR_DIR_NOT_WRITEABLE'
            if not error:
                fileobj.save(filepath)
                url = url_for('main.static', filename='%s/%s' % ('upload', rnd_name))
        else:
            error = 'post error'

        res = """
                <script type="text/javascript">
                window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
                </script>
             """ % (callback, url, error)

        response = make_response(res)
        response.headers["Content-Type"] = "text/html"
        return response
'''
class PostForm(FlaskForm, CKEditor):
    #body = PageDownField("What's on your mind?", validators = [DataRequired()])
    body = TextAreaField('What your mind?')
    submit = SubmitField('Save')
'''
class PostForm(FlaskForm):
    body = CKEditorField('有什么想说的', validators = [DataRequired()])
    submit = SubmitField('发表')

class CommentForm(FlaskForm):
    body = StringField('', validators = [DataRequired()])
    submit = SubmitField('评论')
