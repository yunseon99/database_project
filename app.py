

from datetime import datetime, timedelta, timezone
from flask import flash, redirect, render_template, request, session, Flask
from db_start import BookLog, Category, db, Book, BookStatus, Librarian, Member, Reservation

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:0000@localhost/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'asdf'

db.init_app(app)
@app.context_processor
def inject_user():
    return dict(session=session)

# 홈
@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        return redirect('/books')



# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user_type = data['user_type']

        user = None
        if user_type == 'member':
            user = Member.query.filter_by(email=data['email'], pw=data['pw']).first()
        elif user_type == 'librarian':
            user = Librarian.query.filter_by(email=data['email'], pw=data['pw']).first()

        if user:
            session['user_id'] = user.id
            session['user_type'] = user_type
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')


# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect('/login')


# 회원가입
@app.route('/register/member', methods=['GET', 'POST'])
def register_member():
    if request.method == 'POST':
        data = request.form
        new_member = Member(
            email=data['email'],
            pw=data['pw'],
            name=data['name'],
            birth=datetime.strptime(data['birth'], '%Y-%m-%d'),
            contact=data['contact']
        )
        db.session.add(new_member)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


# 사서 회원가입
@app.route('/register/librarian', methods=['GET', 'POST'])
def register_librarian():
    if request.method == 'POST':
        data = request.form
        new_librarian = Librarian(
            email=data['email'],
            pw=data['pw'],
            name=data['name'],
            birth=datetime.strptime(data['birth'], '%Y-%m-%d'),
            contact=data['contact']
        )
        db.session.add(new_librarian)
        db.session.commit()
        return redirect('/login')
    return render_template('register_librarian.html')


# 도서 목록
@app.route('/books', methods=['GET'])
def books():
    name_query = request.args.get('name') 
    category_query = request.args.get('category') 

    books = Book.query
    if name_query:
        books = books.filter(Book.name.ilike(f'%{name_query}%'))
    if category_query:
        category = Category.query.filter(Category.description.ilike(f'%{category_query}%')).first()
        if category:
            books = books.filter(Book.category_num == category.id)

    books = books.all()
    results = []
    for book in books:
        status = BookStatus.query.filter_by(book_id=book.id).first()
        category_description = (
            Category.query.filter_by(id=book.category_num).first().description
            if book.category_num else "알수없음"
        )
        results.append({
            "id": book.id,
            "name": book.name,
            "author": book.author,
            "publisher": book.publisher,
            "category_description": category_description,
            "status": status.status if status else "알수없음",
        })

    return render_template('books.html', books=results)


# 도서 예약
@app.route('/reserve', methods=['POST'])
def reserve_book():
    if 'user_id' not in session or session['user_type'] != 'member':
        return redirect('/login')

    data = request.form
    book_id = data['book_id']
    member_id = session['user_id']

    existing_reservation = Reservation.query.filter_by(book_id=book_id, member_id=member_id).first()
    if existing_reservation:
        flash("이미 해당 책을 예약했습니다", "warning")
        return redirect('/books')

    try:
        # 새로운 예약 생성
        new_reservation = Reservation(
            book_id=book_id,
            member_id=member_id
        )
        db.session.add(new_reservation)
        db.session.commit()

        flash("예약 성공", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"에러 발생: {str(e)}", "error")

    return redirect('/books')



# 회원 마이페이지
@app.route('/mypage', methods=['GET'])
def mypage():
    if 'user_id' not in session:
        return redirect('/login')
    elif session['user_type'] != 'member':
        return redirect('/librarian/dashboard')

    member_id = session['user_id']


    loaned_books = BookStatus.query.filter_by(member_id=member_id, status='대출 중').all()
    loaned_list = [
        {
            "book_name": Book.query.get(loan.book_id).name,
            "due_date": loan.due_date.strftime('%Y-%m-%d'),
            "book_id": loan.book_id
        }
        for loan in loaned_books
    ]


    overdue_books = BookStatus.query.filter(
        BookStatus.member_id == member_id,
        BookStatus.status == '대출 중',
        BookStatus.due_date < datetime.utcnow()
    ).all()
    
    overdue_list = [
        {
            "book_name": Book.query.get(overdue.book_id).name,
            "book_author": Book.query.get(overdue.bokk_id).author,
            "book_publisher": Book.query.get(overdue.book_id).publisher,
            "due_date": overdue.due_date.strftime('%Y-%m-%d'),
            "book_id": overdue.book_id
        }
        for overdue in overdue_books
    ]


    lost_books = BookStatus.query.filter_by(member_id=member_id, status='분실').all()
    lost_list = [
        {
            "book_name": Book.query.get(lost.book_id).name,
            "book_author": Book.query.get(lost.book_id).author,
            "book_publisher": Book.query.get(lost.book_id).publisher,
            "due_date": lost.due_date.strftime('%Y-%m-%d'),
            "book_id": lost.book_id
        }
        for lost in lost_books
    ]


    reservations = Reservation.query.filter_by(member_id=member_id).all()
    reserved_list = []
    for reservation in reservations:
        book = Book.query.get(reservation.book_id)
        book_status = BookStatus.query.filter_by(book_id=reservation.book_id).first()

        reservation_queue = Reservation.query.filter_by(book_id=reservation.book_id).order_by(Reservation.reservation_date).all()
        position = next((index + 1 for index, res in enumerate(reservation_queue) if res.member_id == member_id), None)

        if position == 1 and book_status and book_status.status == '대출 가능':
            reservation_status = "대출 가능"
        elif position is not None:
            reservation_status = f"예약 순위: {position}"
        else:
            reservation_status = "예약 상태 확인 불가"

        reserved_list.append({
            "book_name": book.name,
            "book_author": book.author,
            "book_publisher": book.publisher,
            "reservation_date": reservation.reservation_date.strftime('%Y-%m-%d %H:%M:%S'),
            "reservation_status": reservation_status,
            "book_id": book.id
        })

    return render_template(
        'mypage.html',
        loaned_list=loaned_list,
        overdue_list=overdue_list,
        lost_list=lost_list,
        reserved_list=reserved_list
    )
#예약 취소
@app.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():
    if 'user_id' not in session or session['user_type'] != 'member':
        return redirect('/login')  

    try:
        reservation_id = request.form['book_id']

        reservation = Reservation.query.filter_by(book_id=reservation_id, member_id=session['user_id']).first()
        if not reservation:
            flash("예약 목록에 존재하지 않습니다", "error")
            return redirect('/mypage')

        db.session.delete(reservation)
        db.session.commit()
        flash("예약 취소 성공", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"오류 발생: {str(e)}", "error")

    return redirect('/mypage')



# 대출 승인
@app.route('/approve_loan', methods=['GET', 'POST'])
def approve_loan():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')

    if request.method == 'POST':
        user_email = request.form['user_email']
        category_num = request.form['category_num']
        call_number = request.form['call_number']


        member = Member.query.filter_by(email=user_email).first()
        if not member:
            return render_template('approve_loan.html', error="회원이 존재하지 않습니다.")

        overdue_books = BookStatus.query.filter(
            BookStatus.member_id == member.id,
            BookStatus.due_date < datetime.utcnow(),
            BookStatus.status == '대출 중'
        ).count()
        if overdue_books > 0:
            return render_template('approve_loan.html', error="연체 중인 도서가 있어 추가 대출이 불가합니다.")


        book = Book.query.filter_by(category_num=category_num, classification=call_number).first()
        if not book:
            return render_template('approve_loan.html', error="해당 분류코드와 식별 코드를 가진 책이 존재하지 않습니다.")

        book_status = BookStatus.query.filter_by(book_id=book.id, status='대출 가능').first()
        if not book_status:
            return render_template('approve_loan.html', error="책이 대출 가능 상태가 아닙니다.")


        reservations = Reservation.query.filter_by(book_id=book.id).order_by(Reservation.reservation_date).all()
        if reservations:

            if reservations[0].member_id != member.id:
                return render_template(
                    'approve_loan.html',
                    error="해당 도서는 예약 대기자가 존재합니다. 1순위 대기자만 대출 가능합니다."
                )

        try:
            book_status.member_id = member.id
            book_status.librarian_id = session['user_id']
            book_status.status = '대출 중'
            book_status.date = datetime
            book_status.due_date = datetime + timedelta(weeks=2)

            if reservations and reservations[0].member_id == member.id:
                db.session.delete(reservations[0])

            db.session.commit()
            return render_template('approve_loan.html', success="대여 성공")
        except Exception as e:
            db.session.rollback()
            return render_template('approve_loan.html', error=f"오류 발생: {str(e)}")

    return render_template('approve_loan.html')

#대출 연장
@app.route('/extend_loan', methods=['POST'])
def extend_loan():
    if 'user_id' not in session or session.get('user_type') != 'member':
        return redirect('/login')

    book_id = request.form['book_id']

    try:
        loan = BookStatus.query.filter_by(book_id=book_id, status='대출 중').first()
        if not loan:
            flash("해당 책은 대출 중이지 않습니다.", "error")
            return redirect('/mypage')


        reservation_exists = Reservation.query.filter_by(book_id=book_id).order_by(Reservation.reservation_date).first()
        if reservation_exists:
            flash("해당 도서는 대기자가 있어 연장할 수 없습니다.", "error")
            return redirect('/mypage')


        if loan.extension < 2:  
            loan.extension += 1
            loan.due_date = loan.due_date + timedelta(weeks=2) 
            db.session.commit()
            flash("연장 성공", "success")
        else:
            flash("연장 한도에 도달했습니다.", "error")

    except Exception as e:
        db.session.rollback()
        flash(f"오류 발생: {str(e)}", "error")

    return redirect('/mypage')

#도서 반납
@app.route('/return', methods=['GET', 'POST'])
def return_book():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')

    if request.method == 'POST':
        category_num = request.form['category_num']
        call_number = request.form['call_number']


        book = Book.query.filter_by(category_num=category_num, classification=call_number).first()
        if not book:
            return render_template('return.html', error="해당 분류 코드와 식별 코드를 가진 도서가 존재하지 않습니다.")


        book_status = BookStatus.query.filter_by(book_id=book.id, status='대출 중').first()
        if not book_status:
            return render_template('return.html', error="해당 도서는 대출 중이지 않습니다.")

        try:
            book_status.member_id = None
            book_status.librarian_id = session['user_id']
            book_status.status = '정리 중'
            book_status.date = datetime.utcnow()
            book_status.due_date = None
            book_status.extension = 0
            db.session.commit()
            return render_template('return.html', success="도서 반납 성공")
        except Exception as e:
            db.session.rollback()
            return render_template('return.html', error=f"오류 발생: {str(e)}")

    return render_template('return.html')

#도서 정리 중 목록
@app.route('/librarian/dashboard', methods=['GET', 'POST'])
def librarian_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login') 

    error = None

    if request.method == 'POST':
        book_id = request.form['book_id']
        new_status = request.form['new_status']

        try:
            book_status = BookStatus.query.filter_by(book_id=book_id, status='정리 중').first()
            if not book_status:
                error = "해당 책은 정리중이지 않거나 존재하지 않습니다."
            else:
                book_status.status = new_status
                book_status.date = datetime.utcnow()
                book_status.librarian_id = session['user_id']
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            error = f"오류 발생: {str(e)}"

    arranging_books = []
    books_in_arrangement = BookStatus.query.filter_by(status='정리 중').all()
    for book_status in books_in_arrangement:
        book = Book.query.get(book_status.book_id)
        if book:
            arranging_books.append({
                "id": book.id,
                "name": book.name
            })

    return render_template('librarian_dashboard.html', arranging_books=arranging_books, error=error)

#도서 추가
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')

    error = None
    success = None

    if request.method == 'POST':
        try:
            data = request.form
            new_book = Book(
                name=data['name'],
                author=data['author'],
                publisher=data['publisher'],
                category_num=data['category_num'],
                classification=data['classification'],
                publication_date=datetime.strptime(data['publication_date'], '%Y-%m-%d')
            )
            db.session.add(new_book)
            db.session.flush()


            new_book_status = BookStatus(
                book_id=new_book.id,
                status='대출 가능',
                librarian_id=session['user_id'],
                date=datetime.now(timezone.utc)
            )
            db.session.add(new_book_status)
            db.session.commit()

            success = "도서 추가 성공"
        except Exception as e:
            db.session.rollback()
            error = f"오류 발생: {str(e)}"

    return render_template('add_book.html', error=error, success=success)

#도서 관리 목록
@app.route('/librarian_books', methods=['GET'])
def librarian_books():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')

    name_query = request.args.get('name')
    category_query = request.args.get('category')
    status_filter = request.args.get('status')

    books_query = Book.query.join(BookStatus, Book.id == BookStatus.book_id)

    if name_query:
        books_query = books_query.filter(Book.name.ilike(f'%{name_query}%'))

    if category_query:
        category = Category.query.filter(Category.description.ilike(f'%{category_query}%')).first()
        if category:
            books_query = books_query.filter(Book.category_num == category.id)

    if status_filter:
        books_query = books_query.filter(BookStatus.status == status_filter)

    books = books_query.all()

    results = []
    for book in books:
        book_status = BookStatus.query.filter_by(book_id=book.id).first()
        results.append({
            "id": book.id,
            "name": book.name,
            "author": book.author,
            "status": book_status.status if book_status else "알수없음",
            "category_num": book.category_num,
            "classification": book.classification,
            "due_date": book_status.due_date.strftime('%Y-%m-%d') if book_status and book_status.due_date else None,
            "member_id": book_status.member_id if book_status else None,
        })

    return render_template('librarian_books.html', books=results, status_filter=status_filter, name_query=name_query, category_query=category_query)

#도서 상태변경
@app.route('/update_book_status', methods=['POST'])
def update_book_status():
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')

    data = request.form
    book_id = data['book_id']
    new_status = data['new_status']
    librarian_id = session['user_id']

    try:
        book_status = BookStatus.query.filter_by(book_id=book_id).first()
        if not book_status:
            flash("오류 발생 책을 찾을 수 없습니다.", "error")
            return redirect('/librarian_books')

        if new_status == '분실':
            if book_status.status == '대출 중':

                book_status.member_id = book_status.member_id
            else:

                book_status.member_id = None
        else:

            book_status.member_id = None

        book_status.status = new_status
        book_status.librarian_id = librarian_id
        book_status.date = datetime.now(timezone.utc)

        db.session.commit()
        flash(f"도서의 상태가 '{new_status}'으(로) 변경되었습니다.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"오류 발생: {str(e)}", "error")

    return redirect('/librarian_books')

#책 세부정보
@app.route('/book_details/<int:book_id>', methods=['GET'])
def book_details(book_id):
    if 'user_id' not in session or session.get('user_type') != 'librarian':
        return redirect('/login')


    book = Book.query.get(book_id)
    if not book:
        flash("책을 찾을 수 없습니다.", "error")
        return redirect('/librarian_books')

    logs = BookLog.query.filter_by(book_id=book_id).order_by(BookLog.log_date.desc()).all()
    log_entries = []
    for log in logs:
        member = Member.query.get(log.member_id)
        librarian = Librarian.query.get(log.librarian_id)

        member_name = member.name if member else "N/A"
        member_email = member.email if member else "N/A"
        librarian_name = librarian.name if librarian else "N/A"
        librarian_email = librarian.email if librarian else "N/A"

        log_entries.append({
            "log_date": log.log_date.strftime('%Y-%m-%d %H:%M:%S'),
            "previous_status": log.previous_status,
            "current_status": log.current_status,
            "member_name": member_name,
            "member_email": member_email,
            "librarian_name": librarian_name,
            "librarian_email": librarian_email
        })

    return render_template('book_details.html', book=book, log_entries=log_entries)


if __name__ == "__main__":
    app.run(debug=True)