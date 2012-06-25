import libunison.password as password
import libunison.mail as mail
import urllib
import yaml

from flask import Flask, render_template, request, g, redirect
from libunison.models import User
from storm.locals import create_database, Store


app = Flask(__name__)


@app.before_request
def setup_request():
    # Read the configuration.
    stream = open('%s/config.yaml' % request.environ['UNISON_ROOT'])
    g.config = yaml.load(stream)
    # Set up the database.
    database = create_database(g.config['database']['string'])
    g.store = Store(database)


@app.after_request
def teardown_request(response):
    # Commit & close the database connection.
    g.store.commit()
    g.store.close()
    return response


@app.route('/')
def homepage():
    return render_template('home.html')


@app.route('/technology')
def technology():
    return render_template('technology.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/news')
def news():
    return render_template('news.html')


@app.route('/tagview')
def tagview():
    return render_template('tagview.html')


@app.route('/qrcode')
def qrcode():
    return redirect('https://play.google.com/store'
            + '/search?q=pname:ch.epfl.unison')


@app.route('/m/signup', methods=['GET', 'POST'])
def signup_form():
    if request.method == 'GET':
        return render_template('signup.html')
    try:
        email = request.form['email']
        pw = request.form['password']
        pw2 = request.form['password_repeat']
    except KeyError:
        return render_template('signup.html',
                error="please fill out all the fields.")
    # Check if passwords match.
    if pw != pw2:
        return render_template('signup.html',
                error="the passwords don't match.")
    # Check that there is no user with that e-mail address.
    elif g.store.find(User, User.email == email).one() is not None:
        return render_template('signup.html', error="this e-mail address is "
                "already used by another account.")
    # Check that the e-mail address is valid.
    elif not mail.is_valid(email):
        return render_template('signup.html',
                error="e-mail address is invalid.")
    # Check that the password is good enough.
    elif not password.is_good_enough(pw):
        return render_template('signup.html', error="passwords need to be "
                "at least 6 characters long.")
    # Check that the terms of use were checked.
    elif not request.form.get('tou'):
        return render_template('signup.html',
                error="you must accept the Terms of Use.")
    # All the checks went through, we can create the user.
    user = User(email, password.encrypt(pw))
    g.store.add(user)
    g.store.flush()  # Needed to get an ID.
    # Default nickname.
    user.nickname = unicode("user%d" % user.id)
    return render_template('success.html', intent=gen_intent(email, pw))


def gen_intent(email, pw):
    pw_enc = urllib.quote(pw.encode('utf-8'))
    email_enc = urllib.quote(email.encode('utf-8'))
    return ("intent:#Intent;action=android.intent.action.VIEW;"
            "package=ch.epfl.unison;S.password=%s;S.email=%s;end"
            % (pw_enc, email_enc))


@app.route('/m/signup', methods=['POST'])
def signup():
    return 
