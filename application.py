import os

from datetime import datetime
from dateutil import relativedelta
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from constants import DB
from helpers import apology, login_required, touch, usd
from models import db, Account, AccountType, Category, CategoryType, Entry, User


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
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    db.init_app(app)

    return app


app = create_app()
Session(app)


def initialize_db():
    response = input(
        "WARNING! Proceeding with this action wiill drop the database, removing all data. Are you sure you would like to continue? (Y/n): "
    )

    if response[0].upper() != "Y":
        print("    |")
        print("    ----> Action cancelled")
        return

    try:
        os.remove(DB)
    except:
        pass

    touch(DB)

    chequing_account = AccountType(
        name="Chequing",
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
    )
    savings_account = AccountType(
        name="Savings", created_date=datetime.utcnow(), modified_date=datetime.utcnow()
    )

    income_category = CategoryType(
        name="Income", created_date=datetime.utcnow(), modified_date=datetime.utcnow()
    )
    expense_category = CategoryType(
        name="Expense", created_date=datetime.utcnow(), modified_date=datetime.utcnow()
    )

    with app.app_context():
        db.create_all()
        db.session.add(chequing_account)
        db.session.add(savings_account)
        db.session.add(income_category)
        db.session.add(expense_category)
        db.session.commit()

    print("    |")
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
        user = User.query.filter_by(id=session["user_id"]).scalar()

        today = datetime.today()
        lower_date_bound = today.replace(day=1)
        upper_date_bound = today + relativedelta.relativedelta(months=1, day=1)

        expense_entries = (
            db.session.query(
                (Category.name).label("category_name"),
                (Account.name).label("account_name"),
                (Category.budget_amount).label("budget_amount"),
                func.sum(Entry.amount).label("amount"),
            )
            .join(Entry.category)
            .join(Category.account)
            .join(Category.category_type)
            .filter(Account.user_id == session["user_id"])
            .filter(CategoryType.name == "Expense")
            .filter(Entry.effective_date >= lower_date_bound)
            .filter(Entry.effective_date < upper_date_bound)
            .group_by(Category.id)
        )

        expense_amount = (
            db.session.query(
                func.sum(Entry.amount).label("amount"),
            )
            .join(Entry.category)
            .join(Category.account)
            .join(Category.category_type)
            .filter(Account.user_id == session["user_id"])
            .filter(CategoryType.name == "Expense")
            .filter(Entry.effective_date >= lower_date_bound)
            .filter(Entry.effective_date < upper_date_bound)
            .first()
        ).amount

        income_amount = (
            db.session.query(
                func.sum(Entry.amount).label("amount"),
            )
            .join(Entry.category)
            .join(Category.account)
            .join(Category.category_type)
            .filter(Account.user_id == session["user_id"])
            .filter(CategoryType.name == "Income")
            .filter(Entry.effective_date >= lower_date_bound)
            .filter(Entry.effective_date < upper_date_bound)
            .first()
        ).amount

        savings = income_amount - expense_amount

    return render_template(
        "index.html",
        username=user.username,
        entries=expense_entries,
        savings=savings,
        income_amount=income_amount,
    )


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
    session.clear()

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

    with app.app_context():
        chequing_account_type = AccountType.query.filter_by(name="Chequing").scalar()
        savings_account_type = AccountType.query.filter_by(name="Savings").scalar()

        income_category_type = CategoryType.query.filter_by(name="Income").scalar()
        expense_category_type = CategoryType.query.filter_by(name="Expense").scalar()

    # setup default accounts and categoies
    chequing = Account(
        name="Chequing",
        description="Chequing and debit deposit account",
        initial_amount=0,
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        user=user,
        account_type=chequing_account_type,
    )

    savings = Account(
        name="Savings",
        description="Savings account",
        initial_amount=0,
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        user=user,
        account_type=savings_account_type,
    )

    income = Category(
        name="Income",
        description="Salary and wage income",
        budget_amount=100,
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        user=user,
        category_type=income_category_type,
        account=chequing,
    )

    misc = Category(
        name="Misc",
        description="Miscellaneous expense items",
        budget_amount=100,
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        user=user,
        category_type=expense_category_type,
        account=chequing,
    )

    try:
        with app.app_context():
            db.session.add(user)
            db.session.add(chequing)
            db.session.add(savings)
            db.session.add(income)
            db.session.add(misc)

            db.session.commit()
    except:
        return apology("Something went wrong")

    return redirect("/login")


@app.route("/add_account", methods=["GET", "POST"])
@login_required
def add_account():
    """
    Add account
    """
    if request.method == "GET":
        user = User.query.filter_by(id=session["user_id"]).scalar()
        account_types = AccountType.query.all()

        return render_template(
            "add_account.html",
            username=user.username,
            account_types=account_types,
        )

    # POST

    name = request.form.get("name")
    description = request.form.get("description")
    account_type_id = request.form.get("account_type")
    initial_amount = request.form.get("initial_amount")

    if not name:
        return apology("Please provide an account name")

    if not description:
        return apology("Please provide an account descriptiona")

    if not initial_amount:
        return apology("Please provide an initial amount")

    with app.app_context():
        account_type = AccountType.query.filter_by(id=account_type_id).scalar()
        account = Account(
            name=name,
            description=description,
            initial_amount=initial_amount,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            user_id=session["user_id"],
            account_type=account_type,
        )
        db.session.add(account)
        db.session.commit()

    return redirect("/accounts")


@app.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    """
    Delete account
    """
    account_id = request.form.get("delete")

    with app.app_context():
        account = Account.query.filter_by(id=account_id).scalar()
        db.session.delete(account)
        db.session.commit()

    return redirect("/accounts")


@app.route("/edit_account", methods=["POST"])
@login_required
def edit_account():
    """
    Edit account
    """
    account_id = request.form.get("edit")
    account_type_id = request.form.get("account_type")
    name = request.form.get("name")
    description = request.form.get("description")
    initial_amount = request.form.get("initial_amount")

    if not name:
        return apology("Please provide an account name")

    with app.app_context():
        account = (
            Account.query.options(joinedload("account_type"))
            .filter(Account.id == account_id)
            .filter(User.id == session["user_id"])
            .scalar()
        )

        account_type = AccountType.query.filter_by(id=account_type_id).scalar()

        account.name = name
        account.description = description
        account.account_type = account_type
        account.initial_amount = initial_amount
        account.modified_date = datetime.utcnow()
        db.session.commit()

    return redirect("/accounts")


@app.route("/accounts", methods=["GET", "POST"])
@login_required
def manage_accounts():
    """
    Manage accounts
    """
    alert_message = ""

    user = User.query.filter_by(id=session["user_id"]).scalar()

    if request.method == "GET":
        with app.app_context():
            accounts = (
                Account.query.options(joinedload("account_type"))
                .filter(Account.user_id == session["user_id"])
                .all()
            )

        return render_template(
            "accounts.html",
            username=user.username,
            alert_message=alert_message,
            accounts=accounts,
        )

    # POST

    account_id = request.form.get("edit")
    with app.app_context():
        account = (
            Account.query.options(joinedload("account_type"))
            .filter(Account.user_id == session["user_id"])
            .filter(Account.id == account_id)
            .scalar()
        )
        account_types = AccountType.query.all()

    return render_template(
        "edit_account.html",
        username=user.username,
        account=account,
        account_types=account_types,
    )


@app.route("/add_category", methods=["GET", "POST"])
@login_required
def add_category():
    """
    Add categories
    """
    if request.method == "GET":
        user = User.query.filter_by(id=session["user_id"]).scalar()
        category_types = CategoryType.query.all()
        accounts = Account.query.filter_by(user_id=session["user_id"]).all()

        return render_template(
            "add_category.html",
            username=user.username,
            category_types=category_types,
            accounts=accounts,
        )

    # POST

    name = request.form.get("name")
    description = request.form.get("description")
    budget_amount = request.form.get("budget_amount")
    category_type_id = request.form.get("category_type")
    account_id = request.form.get("account")

    if not name:
        return apology("Please provide a category name")

    with app.app_context():
        category_type = CategoryType.query.filter_by(id=category_type_id).scalar()
        account = Account.query.filter_by(id=account_id).scalar()
        category = Category(
            name=name,
            description=description,
            budget_amount=budget_amount,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            user_id=session["user_id"],
            category_type=category_type,
            account=account,
        )
        db.session.add(category)
        db.session.commit()

    return redirect("/categories")


@app.route("/delete_category", methods=["POST"])
@login_required
def delete_category():
    """
    Delete categories
    """
    category_id = request.form.get("delete")

    with app.app_context():
        category = Category.query.filter_by(id=category_id).scalar()
        db.session.delete(category)
        db.session.commit()

    return redirect("/categories")


@app.route("/edit_category", methods=["POST"])
@login_required
def edit_category():
    category_id = request.form.get("edit")
    category_type_id = request.form.get("category_type")
    name = request.form.get("name")
    description = request.form.get("description")
    account_id = request.form.get("account")
    budget_amount = request.form.get("budget_amount")

    if not name:
        return apology("Please provide a category name")

    with app.app_context():
        category = (
            Category.query.options(joinedload("category_type"))
            .options(joinedload("account"))
            .filter(Category.id == category_id)
            .filter(Category.user_id == session["user_id"])
            .scalar()
        )

        category_type = CategoryType.query.filter_by(id=category_type_id).scalar()
        account = Account.query.filter_by(id=account_id).scalar()

        category.name = name
        category.description = description
        category.budget_amount = budget_amount
        category.category_type = category_type
        category.modified_date = datetime.utcnow()
        category.account = account
        db.session.commit()

    return redirect("/categories")


@app.route("/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    """
    Manage expense categories
    """
    alert_message = ""

    user = User.query.filter_by(id=session["user_id"]).scalar()

    if request.method == "GET":
        with app.app_context():
            categories = (
                Category.query.options(joinedload("category_type"))
                .options(joinedload("account"))
                .filter(Category.user_id == session["user_id"])
                .all()
            )

        return render_template(
            "categories.html",
            username=user.username,
            alert_message=alert_message,
            categories=categories,
        )

    if request.method == "POST":
        category_id = request.form.get("edit")
        with app.app_context():
            category = (
                Category.query.options(joinedload("category_type"))
                .options(joinedload("account"))
                .filter(Category.user_id == session["user_id"])
                .filter(Category.id == category_id)
                .scalar()
            )
            category_types = CategoryType.query.all()
            accounts = Account.query.filter_by(user_id=session["user_id"]).all()

        return render_template(
            "edit_category.html",
            username=user.username,
            category=category,
            category_types=category_types,
            accounts=accounts,
        )


@app.route("/delete_entry", methods=["POST"])
@login_required
def delete_entry():
    """
    Delete entry
    """
    entry_id = request.form.get("delete")

    with app.app_context():
        entry = Entry.query.filter_by(id=entry_id).scalar()
        db.session.delete(entry)
        db.session.commit()

    return redirect("/entries")


@app.route("/add_entry", methods=["GET", "POST"])
@login_required
def add_entry():
    """
    Add entries
    """
    if request.method == "GET":
        user = User.query.filter_by(id=session["user_id"]).scalar()
        categories = Category.query.filter_by(user_id=session["user_id"]).all()

        return render_template(
            "add_entry.html", username=user.username, categories=categories
        )

    # POST

    category = request.form.get("category")
    amount = request.form.get("amount")
    description = request.form.get("description")

    if not amount:
        return apology("Please provide an entry amount")

    with app.app_context():
        category = Category.query.filter_by(id=category).scalar()
        entry = Entry(
            description=description,
            amount=amount,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            user_id=session["user_id"],
            category=category,
        )
        db.session.add(entry)
        db.session.commit()

    return redirect("/entries")


@app.route("/edit_entry", methods=["POST"])
@login_required
def edit_entry():
    """
    Edit entry
    """
    entry_id = request.form.get("edit")
    amount = request.form.get("amount")
    category = request.form.get("category")
    description = request.form.get("description")
    effective_date = datetime.strptime(
        request.form.get("effective_date"), "%Y-%m-%d %H:%M:%S.%f"
    )

    if not amount:
        return apology("Please provide an entry amount")

    with app.app_context():
        entry = (
            Entry.query.options(joinedload("category"))
            .filter(Entry.id == entry_id)
            .filter(User.id == session["user_id"])
            .scalar()
        )

        entry.amount = amount
        entry.category_id = category
        entry.description = description
        entry.effective_date = effective_date
        entry.modified_date = datetime.utcnow()
        db.session.commit()

    return redirect("/entries")


@app.route("/entries", methods=["GET", "POST"])
@login_required
def manage_entries():
    """
    Manage entries
    """
    alert_message = ""

    user = User.query.filter_by(id=session["user_id"]).scalar()

    if request.method == "GET":
        with app.app_context():
            entries = (
                Entry.query.options(joinedload("category"))
                .filter(Entry.user_id == session["user_id"])
                .order_by(Entry.effective_date.desc())
                .all()
            )
            # categories = Category.query.options(joinedload('category_type')).all()
            # categories = Category.query.filter_by(user_id=session["user_id"]).all()

        return render_template(
            "entries.html",
            username=user.username,
            alert_message=alert_message,
            entries=entries,
        )

    if request.method == "POST":
        entry_id = request.form.get("edit")
        with app.app_context():
            entry = (
                Entry.query.options(joinedload("category"))
                .filter(Entry.user_id == session["user_id"])
                .filter(Entry.id == entry_id)
                .scalar()
            )
            categories = Category.query.all()

        return render_template(
            "edit_entry.html",
            username=user.username,
            entry=entry,
            categories=categories,
        )
