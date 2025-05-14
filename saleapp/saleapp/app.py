from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

# Đường dẫn đến thư mục chứa dữ liệu (data)
DATA_DIR = os.path.join(app.root_path, 'data')
# Đảm bảo thư mục dữ liệu tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

def load_json_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Lỗi: File {filename} không tồn tại.")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi: File {filename} bị lỗi JSON.")
        return []

# Hàm để tải dữ liệu sản phẩm từ file JSON
def load_products(cate_id = None, kw = None, from_price = None, to_price = None):
    """Tải dữ liệu sản phẩm từ file JSON."""
    products_file = os.path.join(DATA_DIR, 'products.json')
    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        return []  # Trả về danh sách rỗng nếu file không tồn tại
    except json.JSONDecodeError:
        print(f"Lỗi: File JSON sản phẩm bị hỏng.  Trả về mặc định.")
        return [] # hoặc xử lý khác
    
    if cate_id:
        products = [p for p in products if p['category_id'] == int(cate_id)]

    if kw:
        products = [p for p in products if p['name'].lower().find(kw.lower()) >= 0]


    if from_price:
        try:
            from_price = float(from_price)
            products = [p for p in products if p['price'] >= from_price]
        except ValueError:
            pass  # Không lọc nếu không hợp lệ
        
    if to_price:
        try:
            to_price = float(to_price)
            products = [p for p in products if p['price'] <= to_price]
        except ValueError:
            pass  # Không lọc nếu không hợp lệ

    return products

def load_categories():
    return load_json_data('categories.json')
# Hàm để lưu dữ liệu sản phẩm vào file JSON
def save_products(products):
    """Lưu dữ liệu sản phẩm vào file JSON."""
    products_file = os.path.join(DATA_DIR, 'products.json')
    with open(products_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# Load products
products = load_products()
if not products:
    # Nếu không có sản phẩm nào trong file, hãy tạo một số sản phẩm mặc định.
    print('khong co san pham')
    save_products(products) # Lưu sản phẩm mặc định vào file
    print("Đã tạo file products.json mặc định.")
# Giỏ hàng (lưu tạm trong session, cần thay bằng cơ sở dữ liệu cho ứng dụng thực tế)
cart = {}
categories = load_categories()

@app.route('/')
def index():
    json_path = os.path.join(app.root_path, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        products = json.load(f)
    return render_template('index.html', products=products, categories=categories)

@app.route("/search")
def search():
    cate_id = request.args.get("category_id")

    kw = request.args.get("keyword")
    from_price = request.args.get("from_price")
    to_price = request.args.get("to_price")
    products = load_products(cate_id=cate_id,
                                    kw = kw,
                                    from_price= from_price,
                                    to_price = to_price)
    
    return render_template('index.html',
                            products=products)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Hiển thị chi tiết sản phẩm."""
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        return render_template("product_detail.html", product=product)
    else:
        return "Sản phẩm không tồn tại!"

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    """Thêm sản phẩm vào giỏ hàng."""
    quantity = int(request.form.get("quantity", 1))
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        if product_id in cart:
            cart[product_id]["quantity"] += quantity
        else:
            cart[product_id] = {"product": product, "quantity": quantity}
        return redirect(url_for("view_cart"))
    else:
        return "Sản phẩm không tồn tại!"

@app.route("/cart")
def view_cart():
    """Hiển thị giỏ hàng."""
    total_price = sum(item["product"]["price"] * item["quantity"] for item in cart.values())
    return render_template("cart.html", cart=cart, total_price=total_price)

@app.route("/update_cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    """Cập nhật số lượng sản phẩm trong giỏ hàng."""
    quantity = int(request.form.get("quantity", 1))
    if product_id in cart:
        if quantity > 0:
            cart[product_id]["quantity"] = quantity
        else:
            del cart[product_id]
    return redirect(url_for("view_cart"))

@app.route("/remove_from_cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    """Xóa sản phẩm khỏi giỏ hàng."""
    if product_id in cart:
        del cart[product_id]
    return redirect(url_for("view_cart"))

@app.route("/checkout")
def checkout():
    """Hiển thị trang thanh toán."""
    if not cart:
        return "Giỏ hàng của bạn đang trống!"

    total_price = sum(item["product"]["price"] * item["quantity"] for item in cart.values())
    return render_template("checkout.html", total_price=total_price)

@app.route("/process_order", methods=["POST"])
def process_order():
    """Xử lý đơn hàng."""
    # Ở đây bạn sẽ thực hiện các bước xử lý đơn hàng thực tế:
    # 1. Lưu đơn hàng vào cơ sở dữ liệu.
    # 2. Trừ số lượng sản phẩm trong kho.
    # 3. Gửi email xác nhận cho khách hàng.
    # 4. Xóa giỏ hàng.
    # ...
    if not cart:
        return "Giỏ hàng của bạn đang trống!"
    print("Đơn hàng đã được xử lý (giả lập). Chi tiết đơn hàng:")
    for item in cart.values():
        print(f"- {item['product']['name']}: {item['quantity']} x {item['product']['price']} = {item['quantity'] * item['product']['price']}")
    print(f"Tổng tiền: {sum(item['product']['price'] * item['quantity'] for item in cart.values())}")
    cart.clear()
    return  redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')


@app.route('/category/<int:cate_id>')
def show_products_by_category(cate_id):
    """Hiển thị sản phẩm theo ID danh mục."""
    print(f"[DEBUG] cate_id nhận được: {cate_id}")
    print(f"[DEBUG] Danh sách categories: {categories}")

    # Lọc sản phẩm theo cate_id (ép kiểu để so sánh chắc chắn)
    filtered_products = [
        product for product in products 
        if int(product.get('category_id', -1)) == cate_id
    ]

    # Tìm tên danh mục
    category = next((cat for cat in categories if int(cat.get('id', -1)) == cate_id), None)
    category_name = category['name'] if category else "Danh mục không tồn tại"

    print(f"[DEBUG] Số sản phẩm lọc được: {len(filtered_products)}")
    print(f"[DEBUG] Tên danh mục: {category_name}")

    return render_template('index.html', products=filtered_products, categories=categories, current_category=category_name)

if __name__ == "__main__":
    app.run(debug=True)
