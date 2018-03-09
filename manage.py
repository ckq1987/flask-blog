import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch = True, include = 'app/*')
    COV.start()
from flask import current_app
from app import create_app, db
from app.models import User, Role, Permission, Post, Comment, Alembic
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import re, pymysql
pymysql.install_as_MySQLdb()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def subImg(name):
    re_img = re.compile('<img.*?/>')
    return re.sub(re_img, u'[图片]', name)

env=app.jinja_env
env.filters['subImg'] = subImg

manager = Manager(app)
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db = db, User = User, Role = Role, Permission = Permission)
manager.add_command('shell', Shell(make_context = make_shell_context))
manager.add_command('db', MigrateCommand)

@app.cli.command()
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity = 2).run(tests)


def create_database():
    db = SQLAlchemy(app)
    Role.insert_roles()
    print(Role.query.all())
    u1 = User(email = current_app.config['FLASKY_ADMIN'], username = 'zhe', password = 'cat', confirmed = True, name = 'huazhaozhe', location = 'Erath', about_me = 'God')
    u2 = User(email = 'huazhaozhe@163.com', username = 'huazhaozhe', password = 'dog', confirmed = True)
    try:
        db.session.add(u1)
        db.session.commit()
    except:
        pass
    try:
        db.session.add(u2)
        db.session.commit()
    except:
        pass
    user = User.query.filter_by(email = current_app.config['FLASKY_ADMIN']).first()
    user.role = Role.query.filter_by(name = 'Administrator').first()
    db.session.add(user)
    db.session.commit()
    User.generate_fake(20)
    Post.generate_fake(200)


@manager.command
def profile(length = 25, profile_dir = None):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [length], profile_dir = profile_dir)
    app.run()

@manager.command
def deploy():
    from app.models import Role, User


    Role.insert_roles()
    try:
        u1 = User(email = current_app.config['FLASKY_ADMIN'], username = 'zhe', password = 'cat', confirmed = True, name = 'huazhaozhe', location = 'Erath', about_me = 'God')
        db.session.add(u1)
        db.session.commit()
    except:
        pass
    try:
        u2 = User(email = 'huazhaozhe@163.com', username = 'huazhaozhe', password = 'dog', confirmed = True)
        db.session.add(u2)
        db.session.commit()
    except:
        pass

    User.add_self_follow()


@manager.command
def test(coverage = False):
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage, Summary:')
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory = covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()

if __name__ == '__main__':
    manager.run()

