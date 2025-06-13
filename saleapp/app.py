from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import json
import os
import io
import sys
import sqlite3 # Keep for initial migration or if user explicitly wants to keep two dbs
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # Để bảo mật tên file
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from functools import wraps

app = Flask(__name__)
# IMPORTANT: Use a strong, randomly generated secret key in production
app.secret_key = 'your_secret_key_here_a_very_long_and_random_string'

DATA_DIR = os.path.join(app.root_path, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Đảm bảo thư mục upload tồn tại

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
# Configure SQLAlchemy for a unified database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unified_database.db' # Changed to a single DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- SQLAlchemy Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) # Added username
    password_hash = db.Column(db.String(128), nullable=False) # Renamed for clarity
    role = db.Column(db.String(20), default='user', nullable=False) # Added role

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- Product and Category Models (if you want to switch from JSON to DB for products) ---
# For now, products/categories are still loaded from JSON as per original code.
# If you decide to manage products in DB, uncomment and use these:
# class Category(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     products = db.relationship('Product', backref='category', lazy=True)
#
# class Product(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     description = db.Column(db.Text)
#     category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


# --- Database Initialization ---
# This part should ideally run once, e.g., using a separate script or on first app run.
# Moved out of before_request to avoid running on every request.
with app.app_context():
    db.create_all() # Creates tables for User (and Product/Category if defined and uncommented)

    # Initial check for admin user. Create if not exists.
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', role='admin')
        admin_user.set_password('admin_password') # IMPORTANT: Change this default password immediately!
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created (username: admin, password: admin_password)")

    # You might also want to populate categories and products here if you switch them to DB
    # Example for categories if you decide to use DB:
    # if not Category.query.first():
    #     db.session.add(Category(name='Electronics'))
    #     db.session.add(Category(name='Books'))
    #     db.session.commit()

# --- JSON utilities (Still used for products and categories as per original code) ---
def load_json_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_products(products_data): # Renamed 'products' to 'products_data' to avoid conflict with global list
    filepath = os.path.join(DATA_DIR, 'products.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, ensure_ascii=False, indent=4)

def load_products(cate_id=None, kw=None, from_price=None, to_price=None):
    products_list = load_json_data('products.json') # Renamed to products_list
    if cate_id:
        # Ensure cate_id is an integer for comparison
        products_list = [p for p in products_list if p.get('category_id') == int(cate_id)]
    if kw:
        products_list = [p for p in products_list if kw.lower() in p['name'].lower()]
    if from_price:
        try:
            from_price = float(from_price)
            products_list = [p for p in products_list if p['price'] >= from_price]
        except (ValueError, KeyError): # Added KeyError in case 'price' is missing
            pass
    if to_price:
        try:
            to_price = float(to_price)
            products_list = [p for p in products_list if p['price'] <= to_price]
        except (ValueError, KeyError): # Added KeyError
            pass
    return products_list

def load_categories():
    return load_json_data('categories.json')

# Load initial data (still from JSON)
products = load_products()
categories = load_categories()
if not products:
    save_products([]) # Ensure products.json is initialized if empty

# --- Routes for Public/Shop Features ---

@app.route('/')
def index():
    # Use load_products() directly in routes to reflect any changes if JSON is externally updated
    # (though typically for production, products would be in a DB)
    all_products = load_products()
    all_categories = load_categories()
    return render_template('index.html', products=all_products, categories=all_categories)

@app.route('/search')
def search():
    cate_id = request.args.get("category_id")
    kw = request.args.get("keyword")
    from_price = request.args.get("from_price")
    to_price = request.args.get("to_price")
    # Pass all products and categories for consistent header/sidebar rendering
    all_products = load_products(cate_id, kw, from_price, to_price)
    all_categories = load_categories()
    return render_template('index.html', products=all_products, categories=all_categories)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    # Load products on demand for detail view
    all_products = load_products()
    product = next((p for p in all_products if p["id"] == product_id), None)
    if product:
        return render_template("product_detail.html", product=product)
    flash("Sản phẩm không tồn tại!", 'danger') # Use flash for user feedback
    return redirect(url_for('index'))

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    quantity = int(request.form.get("quantity", 1))
    all_products = load_products() # Ensure product data is fresh
    product = next((p for p in all_products if p["id"] == product_id), None)

    if product:
        # Initialize cart in session if it doesn't exist
        if 'cart' not in session:
            session['cart'] = {}

        # Convert product to a serializable format for session storage
        product_info = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            # Add other necessary product details if needed, but keep it light for session
        }

        # Update cart in session
        if str(product_id) in session['cart']: # Use string key for dictionary
            session['cart'][str(product_id)]["quantity"] += quantity
        else:
            session['cart'][str(product_id)] = {"product": product_info, "quantity": quantity}

        flash(f'Đã thêm {quantity} x {product["name"]} vào giỏ hàng!', 'success')
        return redirect(url_for("view_cart"))
    flash("Sản phẩm không tồn tại!", 'danger')
    return redirect(url_for('index'))

@app.route("/cart")
def view_cart():
    # Retrieve cart from session
    user_cart = session.get('cart', {})
    total_price = sum(item["product"]["price"] * item["quantity"] for item in user_cart.values())
    return render_template("cart.html", cart=user_cart, total_price=total_price)

@app.route("/update_cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    quantity = int(request.form.get("quantity", 1))
    user_cart = session.get('cart', {})

    if str(product_id) in user_cart:
        if quantity > 0:
            user_cart[str(product_id)]["quantity"] = quantity
            flash("Giỏ hàng đã được cập nhật!", 'success')
        else:
            del user_cart[str(product_id)]
            flash("Sản phẩm đã được xóa khỏi giỏ hàng!", 'success')
        session['cart'] = user_cart # Save updated cart back to session
    else:
        flash("Sản phẩm không có trong giỏ hàng!", 'danger')
    return redirect(url_for("view_cart"))

@app.route("/remove_from_cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    user_cart = session.get('cart', {})
    if str(product_id) in user_cart:
        del user_cart[str(product_id)]
        session['cart'] = user_cart # Save updated cart back to session
        flash("Sản phẩm đã được xóa khỏi giỏ hàng!", 'success')
    else:
        flash("Sản phẩm không có trong giỏ hàng!", 'danger')
    return redirect(url_for("view_cart"))

@app.route("/checkout")
def checkout():
    user_cart = session.get('cart', {})
    if not user_cart:
        flash("Giỏ hàng của bạn đang trống! Vui lòng thêm sản phẩm.", 'warning')
        return redirect(url_for('index'))
    total_price = sum(item["product"]["price"] * item["quantity"] for item in user_cart.values())
    return render_template("checkout.html", total_price=total_price, cart=user_cart)

@app.route("/process_order", methods=["POST"])
def process_order():
    user_cart = session.get('cart', {})
    if not user_cart:
        flash("Giỏ hàng của bạn đang trống! Không thể xử lý đơn hàng.", 'warning')
        return redirect(url_for('index'))

    # Here you would typically save the order to a database
    # For now, we just clear the cart and redirect
    session['cart'] = {} # Clear cart in session
    flash("Đơn hàng của bạn đã được xử lý thành công!", 'success')
    return redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')

@app.route('/category/<int:cate_id>')
def show_products_by_category(cate_id):
    all_categories = load_categories()
    filtered_products = load_products(cate_id=cate_id) # Use load_products with filter
    category = next((cat for cat in all_categories if int(cat.get('id', -1)) == cate_id), None)
    category_name = category['name'] if category else "Danh mục không tồn tại"
    return render_template('index.html', products=filtered_products, categories=all_categories, current_category=category_name)

# --------------------- AUTHENTICATION (Using SQLAlchemy) -------------------------

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, role='user') # Default role
        new_user.set_password(password_input)
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Check users (now from SQLAlchemy DB)
@app.route('/users')
def list_user():
    users = User.query.order_by(User.id.asc()).all() # Query from SQLAlchemy User model
    return render_template('users.html', users=users)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password_input):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role # Get role from DB

            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất!', 'info')
    return redirect(url_for('login'))


#-------------ADMIN-------------#
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash("Bạn không có quyền truy cập trang quản trị!", 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_control():
    return render_template('admin/control.html')

@app.route('/admin/add-product', methods=['GET','POST'])
@admin_required
def admin_add_product():
    current_products = load_json_data('products.json')
    all_categories = load_categories()

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        category_id = int(request.form['category_id'])

        # Generate a new ID for the product FIRST, as it might be used in image filename
        new_id = max([p['id'] for p in current_products]) + 1 if current_products else 1

        image_filename = None # Mặc định không có ảnh
        if 'image' in request.files: # Kiểm tra xem có file ảnh được gửi lên không
            file = request.files['image']
            if file.filename == '':
                flash('Không có file ảnh nào được chọn.', 'warning')
                # Nếu không có file, có thể dùng ảnh placeholder hoặc bỏ qua
                image_filename = f"placeholder_{new_id}.jpg" # Tên file placeholder mặc định
                # Tạo ảnh placeholder nếu cần, hoặc bỏ qua dòng dưới
                # Bạn cần có một ảnh mặc định trong static/images/products/placeholder_id.jpg
            elif file and allowed_file(file.filename):
                # Tạo tên file mới dựa trên ID sản phẩm để dễ quản lý
                # Ví dụ: p1.jpg, p2.jpg
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"p{new_id}.{file_extension}"
                # Sử dụng secure_filename để đảm bảo an toàn, mặc dù chúng ta đã tạo tên file mới
                filename_to_save = secure_filename(image_filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_to_save))
                flash('Ảnh sản phẩm đã được tải lên thành công!', 'info')
            else:
                flash('Loại file ảnh không hợp lệ! Chỉ chấp nhận PNG, JPG, JPEG, GIF.', 'danger')
                return redirect(url_for('admin_add_product')) # Trở lại form nếu file không hợp lệ

        new_product_data = {
            "id": new_id,
            "name": name,
            "price": price,
            "description": description,
            "category_id": category_id,
            "image": url_for('static', filename=f'images/products/{image_filename}') if image_filename else None # Lưu đường dẫn ảnh tĩnh
        }
        # Nếu không có ảnh hoặc lỗi ảnh, "image" có thể là None hoặc một placeholder URL khác

        current_products.append(new_product_data)
        save_products(current_products)

        flash('Sản phẩm đã được thêm thành công!', 'success')
        return redirect(url_for('admin_control'))

    return render_template('admin/add_product.html', categories=all_categories)


@app.route('/admin/manage-products')
@admin_required
def admin_manage_products():
    all_products = load_products()
    all_categories = load_categories()
    # Create a dictionary for quick category name lookup
    category_names = {cat['id']: cat['name'] for cat in all_categories}
    return render_template('admin/manage_products.html', products=all_products, category_names=category_names)

@app.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    current_products = load_json_data('products.json')
    all_categories = load_categories()
    product_to_edit = next((p for p in current_products if p['id'] == product_id), None)

    if not product_to_edit:
        flash('Sản phẩm không tồn tại!', 'danger')
        return redirect(url_for('admin_manage_products'))

    if request.method == 'POST':
        product_to_edit['name'] = request.form['name']
        product_to_edit['price'] = float(request.form['price'])
        product_to_edit['description'] = request.form['description']
        product_to_edit['category_id'] = int(request.form['category_id'])
        # Optionally update image if form provides one
        # product_to_edit['image'] = request.form.get('image', product_to_edit['image'])

        save_products(current_products)
        flash('Sản phẩm đã được cập nhật!', 'success')
        return redirect(url_for('admin_manage_products'))

    return render_template('admin/edit_product.html', product=product_to_edit, categories=all_categories)


@app.route('/admin/delete-product/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    current_products = load_json_data('products.json')
    original_len = len(current_products)
    current_products = [p for p in current_products if p['id'] != product_id]

    if len(current_products) < original_len:
        save_products(current_products)
        flash('Sản phẩm đã được xóa!', 'success')
    else:
        flash('Sản phẩm không tìm thấy để xóa!', 'danger')
    return redirect(url_for('admin_manage_products'))


@app.route('/admin/manage-users') # New route for user management
@admin_required
def admin_manage_users():
    users = User.query.order_by(User.id.asc()).all() # Query from SQLAlchemy User model
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        if user_to_delete.role == 'admin':
            flash('Không thể xóa tài khoản quản trị viên!', 'danger')
        elif user_to_delete.id == session.get('user_id'): # Prevent self-deletion
            flash('Không thể xóa tài khoản của chính bạn!', 'danger')
        else:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash(f'Người dùng "{user_to_delete.username}" đã được xóa thành công!', 'success')
    else:
        flash('Người dùng không tồn tại!', 'danger')
    return redirect(url_for('admin_manage_users'))

if __name__ == "__main__":
    app.run(debug=True)
