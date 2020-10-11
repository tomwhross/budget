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


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(255), unique=False, nullable=False)
    account_type = db.Column(db.String(15), unique=False, nullable=False)
    initial_amount = db.Column(db.Numeric(18, 2), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("accounts", lazy=True))

    def __repr__(self):
        return "<Account %r>" % self.name


class Bucket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(255), unique=False, nullable=False)
    expense_type = db.Column(db.String(15), unique=False, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("buckets", lazy=True))

    def __repr__(self):
        return "<Bucket %r>" % self.name


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), unique=False, nullable=False)
    aamount = db.Column(db.Numeric(18, 2), unique=False, nullable=False)
    effective_date = db.Column(db.DateTime, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)

    bucket_id = db.Column(db.Integer, db.ForeignKey("bucket.id"), nullable=False)
    bucket = db.relationship("Bucket", backref=db.backref("entries", lazy=True))

    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    account = db.relationship("Account", backref=db.backref("entries", lazy=True))

    def __repr__(self):
        return "<Entry %r - %r>" % self.description, self.effective_date
