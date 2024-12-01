import pymysql

# MySQL 데이터베이스 연결 설정
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='0000',  # 실제 MySQL 루트 비밀번호로 교체하세요.
    database='library',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        # 트리거 생성
        trigger = """
        CREATE TRIGGER write_book_log
        AFTER UPDATE ON book_status
        FOR EACH ROW
        BEGIN
            IF OLD.status <> NEW.status THEN
                INSERT INTO book_log (book_id, member_id, librarian_id, log_date, previous_status, current_status)
                VALUES (NEW.book_id, NEW.member_id, NEW.librarian_id, NOW(), OLD.status, NEW.status);
            END IF;
        END;
        """
        cursor.execute(trigger)

        
    connection.commit()

except pymysql.MySQLError as e:
    print(f"Error: {e}")

finally:
    connection.close()
