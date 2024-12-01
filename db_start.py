
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:0000@localhost/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




# 회원 테이블
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    birth = db.Column(db.Date, nullable=False)
    contact = db.Column(db.String(50), nullable=False)

# 사서 테이블
class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    birth = db.Column(db.Date, nullable=False)
    contact = db.Column(db.String(50), nullable=False)

# 카테고리 테이블
class Category(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # DDC에 따른 숫자 (예: 600.12)
    description = db.Column(db.String(255), nullable=False)

# 책 테이블
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    category_num = db.Column(
        db.String(50), 
        db.ForeignKey('category.id'), 
        nullable=False
    )
    classification = db.Column(db.String(255), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('category_num', 'classification', name='uq_category_classification'),
    )

# 단일 상태 관리 테이블
class BookStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer, 
        db.ForeignKey('book.id', ondelete='SET NULL'), 
        unique=True, 
        nullable=True
    )
    member_id = db.Column(
        db.Integer, 
        db.ForeignKey('member.id', ondelete='SET NULL'), 
        nullable=True
    )
    librarian_id = db.Column(
        db.Integer, 
        db.ForeignKey('librarian.id'), 
        nullable=False
    )
    status = db.Column(
        db.Enum('대출 중', '정리 중', '분실', '대출 가능', name='book_status_enum'), 
        nullable=False
    )
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)
    extension = db.Column(db.Integer, default=0)

# 예약 테이블
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer, 
        db.ForeignKey('book.id'), 
        nullable=False
    )
    member_id = db.Column(
        db.Integer, 
        db.ForeignKey('member.id'), 
        nullable=False
    )
    reservation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# 로그 테이블 (책별 상태 변경 이력 기록)
class BookLog(db.Model):
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(
        db.Integer, 
        db.ForeignKey('book.id', ondelete='CASCADE'), 
        nullable=False
    )
    member_id = db.Column(
        db.Integer, 
        db.ForeignKey('member.id', ondelete='SET NULL'), 
        nullable=True
    )
    librarian_id = db.Column(
        db.Integer, 
        db.ForeignKey('librarian.id', ondelete='SET NULL'), 
        nullable=True
    )
    log_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    previous_status = db.Column(db.String(50), nullable=False)
    current_status = db.Column(db.String(50), nullable=False)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
