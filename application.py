import os

from datetime import datetime
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from constants import DB
from helpers import apology, login_required, touch, usd
from models import db, Bucket, User


def create_app():
    # configure the app
    app = Flask(__name__)

    # ensure templates are auto-reloaded
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # custom filter
    app.jinja_env.filters["usd"] = usd

    # configure session to use filesystem (instead of signed cookies)
    app.config["SESSION_FILE_DIR"] = mkdtemp()
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"

    # configure the db
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB}"
    db.init_app(app)

    return app


app = create_app()
Session(app)


def initialize_db():
    response = input(
        "WARNING! Proceeding with this action wiill drop the database, removing all data. Are you sure you would like to continue? (Y/n): "
    )

    if response[0].upper() != "Y":
        print("    ----> Action cancelled")
        return

    try:
        os.remove(DB)
    except:
        pass

    touch(DB)

    with app.app_context():
        db.create_all()

    print("    ----> Action completed")


# ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    with app.app_context():
        user = User.query.filter_by(id=session["user_id"])

    return render_template("index.html", user_email=user.value("email"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        with app.app_context():
            user = User.query.filter_by(username=request.form.get("username"))

        # Ensure username exists and password is correct
        if user.count() != 1 or not check_password_hash(
            user.value("password"), request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user.value("id")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    alert_message = ""

    if request.method == "GET":
        return render_template("register.html", alert_message=alert_message)

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not confirm_password:
        alert_message = "You must confirm your password"

    if not password:
        alert_message = "You must provide a password"

    if not email:
        alert_message = "You must provide an email address"

    if not username:
        alert_message = "You must provide a username"

    if password != confirm_password:
        alert_message = "Your passwords must match"

    if alert_message:
        return render_template("register.html", alert_message=alert_message)

    with app.app_context():
        check = User.query.filter_by(username=username).first()

    if check:
        return render_template("register.html", alert_message="Username already taken")

    hashed_password = generate_password_hash(password)

    user = User(
        username=username,
        email=email,
        password=hashed_password,
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
    )

    try:
        with app.app_context():
            db.session.add(user)
            db.session.commit()
    except:
        return apology("Something went wrong")

    return redirect("/login")


@app.route("/buckets", methods=["GET", "POST"])
@login_required
def manage_buckets():
    """
    Manage expense buckets
    """
    alert_message = ""

    if request.method == "GET":
        with app.app_context():
            buckets = Bucket.query.filter_by(user_id=session["user_id"]).all()

            print(buckets)

        return render_template(
            "index.html", alert_message=alert_message, buckets=buckets
        )
