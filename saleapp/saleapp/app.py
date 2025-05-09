from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

app = Flask(__name__)

# Đường dẫn đến thư mục chứa dữ liệu (data)
DATA_DIR = os.path.join(app.root_path, 'data')
# Đảm bảo thư mục dữ liệu tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

# Hàm để tải dữ liệu sản phẩm từ file JSON
def load_products():
    """Tải dữ liệu sản phẩm từ file JSON."""
    products_file = os.path.join(DATA_DIR, 'products.json')
    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Trả về danh sách rỗng nếu file không tồn tại
    except json.JSONDecodeError:
        print(f"Lỗi: File JSON sản phẩm bị hỏng.  Trả về mặc định.")
        return [] # hoặc xử lý khác

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

@app.route('/')
def index():
    json_path = os.path.join(app.root_path, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        products = json.load(f)
    return render_template('index.html', products=products)


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
    return "Cảm ơn bạn đã mua hàng!"

if __name__ == "__main__":
    app.run(debug=True)
