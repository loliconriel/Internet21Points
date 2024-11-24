from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    money = db.Column(db.String(50), default="0")

    def add_money(self, amount):
        current_money = int(self.money)
        current_money += amount
        self.money = str(current_money)

    def subtract_money(self, amount):
        current_money = int(self.money)
        current_money -= amount
        self.money = str(current_money)