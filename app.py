import os
import datetime
import logging
import click
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


# --- Flask app ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'posts.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
app.config['SQLALCHEMY_ENGINE_OPTIONS'].setdefault('pool_pre_ping', True)
app.config['SQLALCHEMY_ENGINE_OPTIONS'].setdefault('pool_recycle', 280)

# --- Cache ---
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    app.config.update({
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': redis_url,
    })
else:
    app.config.update({'CACHE_TYPE': 'SimpleCache'})

cache = Cache(app)
db = SQLAlchemy(app)

# Use simple stdout logging for development
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# helper: load current user before requests and inject into templates
@app.before_request
def load_current_user():
    user_id = session.get('user_id')
    if user_id:
        g.user = User.query.get(user_id)
    else:
        g.user = None


@app.context_processor
def inject_user():
    return dict(current_user=g.get('user', None))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get('user'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

# --- POPRAVEK: Inicializacija baze mora biti v globalnem obsegu ---
# To se izvede, ko Gunicorn uvozi aplikacijo (ne glede na __main__)
with app.app_context():
    try: 
        db.create_all()
    except Exception:
        # Če pride do race-conditiona (več workerjev hkrati), ignoriramo napako
        pass
# ------------------------------------------------------------------

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('create'))

        # Attach owner information if available
        post = Post(
            title=title,
            content=content,
            user_id=(g.user.id if g.get('user') else None),
            username=(g.user.username if g.get('user') else None),
        )
        db.session.add(post)
        db.session.commit()

        try:
            if hasattr(cache, 'delete'):
                cache.delete('index')
        except Exception:
            # non-fatal for dev
            pass

        return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        # Prefer next from form (preserved), fallback to query string
        next_url = request.form.get('next') or request.args.get('next') or url_for('index')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        session.clear()
        session['user_id'] = user.id
        session.modified = True
        flash('Logged in', 'success')
        return redirect(next_url)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>/reply', methods=['POST'])
@login_required
def post_reply(post_id):
    post = Post.query.get_or_404(post_id)
    content = (request.form.get('content') or '').strip()
    if not content:
        flash('Reply cannot be empty', 'error')
        return redirect(url_for('post_view', post_id=post_id))
    reply = Reply(post_id=post.id, user_id=g.user.id if g.user else None, username=(g.user.username if g.user else None), content=content)
    db.session.add(reply)
    db.session.commit()
    flash('Reply added', 'success')
    return redirect(url_for('post_view', post_id=post_id))

@app.route('/post/<int:post_id>')
def post_view(post_id):
    post = Post.query.get_or_404(post_id)
    replies = Reply.query.filter_by(post_id=post.id).order_by(Reply.created_at.asc()).all()
    return render_template('post.html', post=post, replies=replies)

@app.cli.command('init-db')
def init_db():
    """Create the SQLite database tables."""
    db.create_all()
    print('Database created at', app.config['SQLALCHEMY_DATABASE_URI'])


@app.cli.command('reset-db')
def reset_db():
    """Drop all tables and recreate the database. Useful for development."""
    click.confirm('This will DROP all data. Continue?', abort=True)
    db.drop_all()
    db.create_all()
    print('Database reset: all tables dropped and recreated')

if __name__ == '__main__':
    # Ta del se izvede le, če poženeš 'python app.py'
    # Gunicorn tega dela NE vidi, zato je create_all zgoraj v global scope.
    app.run(host='0.0.0.0', port=5000, debug=True)