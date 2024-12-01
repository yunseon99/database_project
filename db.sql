--데이터베이스 구조 설명

CREATE TABLE Member (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    pw VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    birth DATE NOT NULL,
    contact VARCHAR(50) NOT NULL
);

CREATE TABLE Librarian (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    pw VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    birth DATE NOT NULL,
    contact VARCHAR(50) NOT NULL
);

CREATE TABLE Category (
    id VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE Book (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    category_num VARCHAR(50) NOT NULL,
    classification VARCHAR(255) NOT NULL,
    publication_date DATE NOT NULL,
    CONSTRAINT uq_category_classification UNIQUE (category_num, classification),
    FOREIGN KEY (category_num) REFERENCES Category(id)
);

CREATE INDEX idx_book_name ON Book (name);

CREATE TABLE BookStatus (
    id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT UNIQUE,
    member_id INT,
    librarian_id INT NOT NULL,
    status ENUM('대출 중', '정리 중', '분실', '대출 가능') NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    extension INT DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES Book(id) ON DELETE SET NULL,
    FOREIGN KEY (member_id) REFERENCES Member(id) ON DELETE SET NULL,
    FOREIGN KEY (librarian_id) REFERENCES Librarian(id)
);

CREATE TABLE Reservation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    reservation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES Book(id),
    FOREIGN KEY (member_id) REFERENCES Member(id)
);

CREATE TABLE BookLog (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT,
    librarian_id INT,
    log_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    previous_status VARCHAR(50) NOT NULL,
    current_status VARCHAR(50) NOT NULL,
    FOREIGN KEY (book_id) REFERENCES Book(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES Member(id) ON DELETE SET NULL,
    FOREIGN KEY (librarian_id) REFERENCES Librarian(id) ON DELETE SET NULL
);

CREATE TRIGGER write_book_log
        AFTER UPDATE ON book_status
        FOR EACH ROW
        BEGIN
            IF OLD.status <> NEW.status THEN
                INSERT INTO book_log (book_id, member_id,
                librarian_id, log_date, previous_status, current_status)

                VALUES (NEW.book_id, NEW.member_id, NEW.librarian_id,
                NOW(), OLD.status, NEW.status);
            END IF;
        END;