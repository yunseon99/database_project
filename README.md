# database_project
데이터베이스 설계 기말 프로젝트
MYSQL 사용

파이썬 가상환경을 세팅하고 가상환경 활성화 .venv\Scripts\Activate 입력
python db_start.py 입력해서 데이터 베이스 테이블 생성(데이터베이스 이름은 library 비밀번호: 0000 사용자: root로 설정 되어있다)
이후 ctrl+c를 눌러 서버를 끈다.
다른 db를 사용한다면 app.py, create_procedure.py, db_start.py, insert_catrgory.py 상단의 설정을 변경해야한다.
python create_procedure.py 입력해서 트리거 생성
python insert_category.py 입력해서 분야 테이블에 정보 저장
python app.py 입력해 서버를 키고
http://localhost:5000/login url로 접속하면 웹사이트를 확인해 볼 수 있다.
