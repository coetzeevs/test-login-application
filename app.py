from flask import Flask, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, \
    current_user, login_required
from oauth import OAuthSignIn
import os

app = Flask(__name__)
driver = 'postgresql+psycopg2://'
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config[
    'SQLALCHEMY_DATABASE_URI'] = \
    driver \
    + os.environ['RDS_USERNAME'] + ':' + os.environ['RDS_PASSWORD'] \
    + '@' + os.environ['RDS_HOSTNAME'] + ':' + os.environ['RDS_PORT'] \
    + '/' + os.environ['RDS_DB_NAME']

# 'postgresql+psycopg2://mydbinstance:Mini1300!@test-instance.ch1ktyvsreco.eu-west-1.rds.amazonaws.com:5432/test_instance'
app.config['OAUTH_CREDENTIALS'] = {
    'google': {
        'id': os.environ['GOOGLE_ID'],
        'secret': os.environ['GOOGLE_SECRET']
    }
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    username, email = oauth.callback()
    if email is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(email=email).first()
    if not user:
        nickname = username
        if nickname is None or nickname == "":
            nickname = email.split('@')[0]
        user = User(nickname=nickname, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug='TRUE')
