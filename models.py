# apps.members.models
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username


class AccountType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<AccountType %r>" % self.name


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(255), unique=False, nullable=False)
    initial_amount = db.Column(db.Numeric(18, 2), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("accounts", lazy=True))

    account_type_id = db.Column(
        db.Integer, db.ForeignKey("account_type.id"), nullable=False
    )
    account_type = db.relationship(
        "AccountType", backref=db.backref("accounts", lazy=True)
    )

    def __repr__(self):
        return "<Account %r>" % self.name


class CategoryType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<CategoryType %r>" % self.name


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(255), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("categories", lazy=True))

    category_type_id = db.Column(
        db.Integer, db.ForeignKey("category_type.id"), nullable=False
    )
    category_type = db.relationship(
        "CategoryType", backref=db.backref("categories", lazy=True)
    )

    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    account = db.relationship("Account", backref=db.backref("categories", lazy=True))

    def __repr__(self):
        return "<Category %r>" % self.name


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), unique=False, nullable=False)
    amount = db.Column(db.Numeric(18, 2), unique=False, nullable=False)
    effective_date = db.Column(db.DateTime, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("entries", lazy=True))

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category = db.relationship("Category", backref=db.backref("entries", lazy=True))

    def __repr__(self):
        return "<Entry %r - %r>" % self.description, self.effective_date
