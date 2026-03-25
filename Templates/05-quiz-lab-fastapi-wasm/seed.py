from app.database import database_path, init_db, seed_db

db_path = database_path()
init_db(db_path)
seed_db(db_path)
print("QuizLab database ready.")
