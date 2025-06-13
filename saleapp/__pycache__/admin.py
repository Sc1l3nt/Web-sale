import sqlite3
from werkzeug.security import generate_password_hash

# Kết nối tới database (đảm bảo đúng tên file và đường dẫn)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Tạo user admin
username = 'admin'
password = '123456'
hashed_password = generate_password_hash(password)

try:
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    print("✅ Tạo user admin thành công!")
except sqlite3.IntegrityError:
    print("⚠️  User 'admin' đã tồn tại.")
finally:
    conn.close()
