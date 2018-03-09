from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import Role, User, Post, Permission, Comment, Follow
from ..decorators import admin_required, permission_required

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >=current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response

@main.route('/', methods = ['GET', 'POST'])
def index():
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body = form.body.data, author = current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type = int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page = current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False
            )
    posts = pagination.items
    return render_template('index.html', form = form, posts = posts, show_followed = show_followed, pagination = pagination)

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        abort(404)
    if user.email == current_app.config['FLASKY_ADMIN'] and user.role is None:
        user.role = Role.query.filter_by('Administrator').first()
        db.session.add(user)
        db.session.commit()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user = user, posts = posts)

@main.route('/edit-profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('你的个人信息已经更新')
        return redirect(url_for('.user', username = current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form = form)

@main.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user = user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('个人信息已经更新')
        return redirect(url_for('.user', username = user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form = form, user = user)

@main.route('/user/enable/<int:id>')
@login_required
@admin_required
def user_enable(id):
    user = User.query.get_or_404(id)
    user.disabled = False
    db.session.add(user)
    db.session.commit()
    posts = Post.query.filter_by(Post.timestamp.desc()).all()
    return render_template('user.html', user = user, posts = posts)

@main.route('/user/disable/<int:id>')
@login_required
@admin_required
def user_disable(id):
    user = User.query.get_or_404(id)
    user.disabled = True
    db.session.add(user)
    db.session.commit()
    posts = Post.query.filter_by(Post.timestamp.desc()).all()
    return render_template('user.html', user = user, posts = posts)


@main.route('/user/delete/<int:id>')
@login_required
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    posts = Post.query.filter_by(author_id = user.id).all()
    for post in posts:
        db.session.delete(post)
    db.session.commit()
    comments = Comment.query.filter_by(author_id = user.id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()
    followers = Follow.query.filter_by(follower_id = user.id).all()
    for follower in followers:
        db.session.delete(follower)
    db.session.commit()
    followeds = Follow.query.filter_by(followed_id = user.id).all()
    for followed in followeds:
        db.session.delete(followed)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()
    flash('User name: %s, id %s, eamil: %s deleted!' % (user.id, user.username, user.email))
    return redirect(url_for('.index'))

@main.route('/user/delete_posts/<int:id>')
@login_required
def user_delete_posts(id):
    user = User.query.get_or_404(id)
    if current_user.username != user.username and not current_user.can(Permission.ADMIN):
        abort(403)
    posts = Post.query.filter_by(author_id = user.id).all()
    for post in posts:
        comments = Comment.query.filter_by(post_id = post.id).all()
        for comment in comments:
            db.session.delete(comment)
        db.session.delete(post)
        db.session.commit()
    flash('所有Blog已经被删除')
    return render_template('user.html', user = user)

@main.route('/user/delete_comments/<int:id>')
@login_required
def user_delete_comments(id):
    user = User.query.get_or_404(id)
    if current_user.username != user.username and not current_user.can(Permission.ADMIN):
        abort(403)
    comments = Comment.query.filter_by(author_id = user.id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()
    flash('所有评论已经删除')
    return render_template('user.html', user = user)


@main.route('/edit/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('Blog已经更新')
        return redirect(url_for('.post', id = post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form = form)

'''
@main.route('/ckupload/', methods=['POST', 'OPTIONS'])
@login_required
def ckupload():
    form = PostForm()
    response = form.upload(endpoint=main)
    return response
'''

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有这个用户')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type = int)
    pagination = user.followers.paginate(page, per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out = False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user = user, title = 'Followers of ', endpoint = '.followers', pagination = pagination, follows = follows)

@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有这个用户')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type = int)
    pagination = user.followed.paginate(page, per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out = False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user = user, title = 'Followed by', endpoint = '.followed_by', pagination = pagination, follows = follows)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    #uesr = User.query.filter_by(username = username).first()
    u = User.query.filter_by(username = username).first()
    if u is None:
        flash('没有这个用户')
        return redirect(url_for('.index'))
    if current_user.is_following(u):
        flash('你已经关注这个用户')
        return redirect(url_for('.user', username = username))
    current_user.follow(u)
    db.session.commit()
    flash('你正在关注这个用户: %s' % username)
    return redirect(url_for('.user', username = username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('没有这个用户')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你没有关关注这个用户')
        return redirect(url_for('.user', username = username))
    current_user.unfollow(user)
    db.session.commit()
    flash('你不在关注这个用户: %s' % username)
    return redirect(url_for('.user', username = username))

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age = 30 * 24 * 60 * 60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age = 30 * 24 * 60 * 60)
    return resp

@main.route('/post/<int:id>', methods = ['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body = form.body.data, post = post, author = current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('评论成功,请返回评论第一页查看你的评论')
        return redirect(url_for('.post', id = post.id, page = -1))
    page = request.args.get('page', 1, type = int)
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items
    return render_template('post.html', posts = [post], form = form, comments = comments, pagination = pagination)

@main.route('/moderate/comments')
@login_required
@permission_required(Permission.MODERATE)
def moderate_comments():
    page = request.args.get('page', 1, type = int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items
    return render_template('moderate.html', comments = comments, pagination = pagination, page = page)

@main.route('/moderate/comments/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate_comments', page = request.args.get('page', 1, type = int)))

@main.route('/moderate/comments/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate_comments', page = request.args.get('page', 1, type = int)))

@main.route('/moderate/comments/delete/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment_delete(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('.moderate_comments', page = request.args.get('page', 1, type = int)))


@main.route('/post/enable/<int:id>')
@login_required
def post_enable(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    post.disabled = False
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('.index', page = request.args.get('page', 1, type = int)))

@main.route('/post/disable/<int:id>')
@login_required
def post_disable(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    post.disabled = True
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('.index', page = request.args.get('page', 1, type = int)))

@main.route('/post/delete/<int:id>')
@login_required
def post_delete(id):
    post = Post.query.get_or_404(id)
    comments = Comment.query.filter_by(post_id = post.id).all()
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()
    db.session.delete(post)
    db.session.commit()
    flash('Blog已经被删除')
    return redirect(url_for('.index', page = request.args.get('page', 1, type = int)))

@main.route('/comment/enable/<int:id>')
@login_required
def comment_enable(id):
    comment = Comment.query.get_or_404(id)
    post = Post.query.get_or_404(comment.post_id)
    form = CommentForm()
    if current_user != comment.author and not current_user.can(Permission.ADMIN):
        abort(403)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    page = request.args.get('page', 1, type = int)
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items
    return render_template('post.html', posts = [post], form = form, comments = comments, pagination = pagination)

@main.route('/comment/disable/<int:id>')
@login_required
def comment_disable(id):
    comment = Comment.query.get_or_404(id)
    post = Post.query.get_or_404(comment.post_id)
    form = CommentForm()
    if current_user != comment.author and not current_user.can(Permission.ADMIN):
        abort(403)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    page = request.args.get('page', 1, type = int)
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items
    return render_template('post.html', posts = [post], form = form, comments = comments, pagination = pagination)


@main.route('/comment/delete/<int:id>')
@login_required
def comment_delete(id):
    comment = Comment.query.get_or_404(id)
    post = Post.query.get_or_404(comment.post_id)
    form = CommentForm()
    if current_user != comment.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已经删除')
    page = request.args.get('page', 1, type = int)
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items
    return render_template('post.html', posts = [post], form = form, comments = comments, pagination = pagination)
