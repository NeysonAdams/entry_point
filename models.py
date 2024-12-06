from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False)
    telegram_id = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True)
    role = db.Column(db.String(255))
    registration_step=db.Column(db.String(255))

    access_point = db.relationship('AccessPoint', backref='user_subscription', uselist=False)
    def __str__(self):
        return self.name


access_point_users = db.Table('access_point_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('accessPoint_id', db.Integer, db.ForeignKey('accessPoint.id'), primary_key=True)
)

class AccessPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creation_date=db.Column(db.DateTime)
    longitude = db.Column(db.String(255))
    latitude = db.Column(db.String(255))

    students = db.relationship('User', secondary=access_point_users, backref=db.backref('users', lazy='dynamic'))

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)