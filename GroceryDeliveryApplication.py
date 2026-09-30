from flask import Flask, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "grocery_delivery_project_2026"

DATABASE = "grocery_delivery.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            delivery_slot TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # Add sample products only when the table is empty
    product_count = connection.execute(
        "SELECT COUNT(*) AS count FROM products"
    ).fetchone()["count"]

    if product_count == 0:
        products = [
            ("Rice", "Grains", 65, 50),
            ("Wheat Flour", "Grains", 55, 40),
            ("Milk", "Dairy", 30, 60),
            ("Bread", "Bakery", 40, 30),
            ("Apples", "Fruits", 120, 35),
            ("Bananas", "Fruits", 50, 45),
            ("Potatoes", "Vegetables", 35, 70),
            ("Tomatoes", "Vegetables", 45, 55),
            ("Biscuits", "Snacks", 30, 80),
            ("Cooking Oil", "Grocery", 150, 35)
        ]

        connection.executemany("""
            INSERT INTO products
            (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """, products)

    connection.commit()
    connection.close()


# =========================================================
# LOGIN CHECK
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# CART FUNCTIONS
# =========================================================

def get_cart():

    cart = session.get("cart", {})

    connection = get_db()

    items = []
    total = 0

    for product_id, quantity in cart.items():

        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product:

            quantity = int(quantity)

            subtotal = product["price"] * quantity

            total += subtotal

            items.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })

    connection.close()

    return items, total


# =========================================================
# WEBSITE STYLE
# =========================================================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f7f5;
    color: #222;
}

nav {
    background: #176b45;
    color: white;
    padding: 15px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 23px;
    font-weight: bold;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 18px;
}

.container {
    width: 86%;
    max-width: 1100px;
    margin: 30px auto;
}

.hero {
    background: white;
    padding: 50px 25px;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 25px;
}

.hero h1 {
    color: #176b45;
    font-size: 35px;
}

.grid {
    display: grid;
    grid-template-columns:
    repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.card h3 {
    color: #176b45;
}

.price {
    font-size: 20px;
    font-weight: bold;
    color: #176b45;
}

button,
.btn {
    background: #176b45;
    color: white;
    border: none;
    padding: 10px 17px;
    border-radius: 7px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
}

button:hover,
.btn:hover {
    background: #0d4e31;
}

input,
select {
    width: 100%;
    padding: 11px;
    margin: 7px 0 15px;
    border: 1px solid #bbb;
    border-radius: 6px;
}

.form-box {
    background: white;
    padding: 30px;
    border-radius: 12px;
    max-width: 500px;
    margin: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

th,
td {
    padding: 13px;
    border-bottom: 1px solid #ddd;
    text-align: left;
}

.total {
    font-size: 23px;
    font-weight: bold;
    text-align: right;
    margin: 20px 0;
}

.message {
    background: #fff3cd;
    padding: 12px;
    border-radius: 7px;
    margin-bottom: 15px;
}

footer {
    margin-top: 50px;
    background: #153d2c;
    color: white;
    padding: 20px;
    text-align: center;
}

</style>
"""


# =========================================================
# PAGE TEMPLATE
# =========================================================

def page(title, content):

    messages = ""

    for message in session.pop("_flashes", []):
        messages += f"""
        <div class="message">{message[1]}</div>
        """

    logged_in_links = ""

    if "user_id" in session:

        logged_in_links = f"""
        <a href="/orders">My Orders</a>
        <a href="/logout">Logout</a>
        """

    else:

        logged_in_links = """
        <a href="/login">Login</a>
        <a href="/register">Register</a>
        """

    cart_count = len(session.get("cart", {}))

    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{title} - FreshCart</title>

{STYLE}

</head>

<body>

<nav>

<div class="logo">
FreshCart
</div>

<div>

<a href="/">Home</a>

<a href="/products">
Products
</a>

<a href="/cart">
Cart ({cart_count})
</a>

{logged_in_links}

</div>

</nav>

<div class="container">

{messages}

{content}

</div>

<footer>

Grocery Delivery Application
<br>
Industrial Internship Project
<br>
Praveen Kumar

</footer>

</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    content = """

    <div class="hero">

        <h1>
        Fresh Groceries Delivered to Your Door
        </h1>

        <p>
        Shop daily grocery essentials
        from one convenient platform.
        </p>

        <br>

        <a class="btn" href="/products">
        Start Shopping
        </a>

    </div>

    <div class="grid">

        <div class="card">
            <h3>Easy Shopping</h3>
            <p>
            Browse grocery products and
            add them to your shopping cart.
            </p>
        </div>

        <div class="card">
            <h3>Flexible Delivery</h3>
            <p>
            Select a suitable delivery slot
            while placing your order.
            </p>
        </div>

        <div class="card">
            <h3>Simple Checkout</h3>
            <p>
            Review your cart and choose
            a payment method.
            </p>
        </div>

    </div>

    """

    return page("Home", content)


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:

            flash("All fields are required.")

            return redirect(url_for("register"))

        connection = get_db()

        try:

            connection.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                generate_password_hash(password)
            ))

            connection.commit()

            flash("Registration successful.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("This email is already registered.")

        finally:

            connection.close()

    content = """

    <div class="form-box">

        <h2>Create Account</h2>

        <form method="post">

            <label>Name</label>

            <input
                type="text"
                name="name"
                required
            >

            <label>Email</label>

            <input
                type="email"
                name="email"
                required
            >

            <label>Password</label>

            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                Register
            </button>

        </form>

        <p>
        Already registered?
        <a href="/login">Login</a>
        </p>

    </div>

    """

    return page("Register", content)


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Login successful.")

            return redirect(url_for("products"))

        flash("Invalid email or password.")

    content = """

    <div class="form-box">

        <h2>Login</h2>

        <form method="post">

            <label>Email</label>

            <input
                type="email"
                name="email"
                required
            >

            <label>Password</label>

            <input
                type="password"
                name="password"
                required
            >

            <button type="submit">
                Login
            </button>

        </form>

        <p>
        New user?
        <a href="/register">
        Create an account
        </a>
        </p>

    </div>

    """

    return page("Login", content)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products():

    connection = get_db()

    products = connection.execute("""
        SELECT * FROM products
        ORDER BY category, name
    """).fetchall()

    connection.close()

    cards = ""

    for product in products:

        cards += f"""

        <div class="card">

            <h3>
            {product["name"]}
            </h3>

            <p>
            Category:
            {product["category"]}
            </p>

            <p>
            Available:
            {product["stock"]}
            </p>

            <p class="price">
            ₹{product["price"]:.2f}
            </p>

            <form
                method="post"
                action="/add-to-cart"
            >

                <input
                    type="hidden"
                    name="product_id"
                    value="{product["id"]}"
                >

                <input
                    type="number"
                    name="quantity"
                    value="1"
                    min="1"
                    max="{product["stock"]}"
                >

                <button type="submit">
                    Add to Cart
                </button>

            </form>

        </div>

        """

    content = f"""

    <h1>Grocery Products</h1>

    <p>
    Select products and add them to your cart.
    </p>

    <div class="grid">

    {cards}

    </div>

    """

    return page("Products", content)


# =========================================================
# ADD TO CART
# =========================================================

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():

    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    connection = get_db()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    if not product:

        flash("Product not found.")

        return redirect(url_for("products"))

    if quantity < 1 or quantity > product["stock"]:

        flash("Invalid quantity.")

        return redirect(url_for("products"))

    cart = session.get("cart", {})

    current_quantity = int(
        cart.get(product_id, 0)
    )

    new_quantity = current_quantity + quantity

    if new_quantity > product["stock"]:

        flash("Requested quantity is not available.")

        return redirect(url_for("products"))

    cart[product_id] = new_quantity

    session["cart"] = cart

    flash(
        product["name"] +
        " added to cart."
    )

    return redirect(url_for("products"))


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    items, total = get_cart()

    rows = ""

    for item in items:

        rows += f"""

        <tr>

            <td>
            {item["name"]}
            </td>

            <td>
            ₹{item["price"]:.2f}
            </td>

            <td>

                <form
                    method="post"
                    action="/update-cart"
                >

                    <input
                        type="hidden"
                        name="product_id"
                        value="{item["id"]}"
                    >

                    <input
                        type="number"
                        name="quantity"
                        value="{item["quantity"]}"
                        min="1"
                        style="width:80px;"
                    >

                    <button>
                    Update
                    </button>

                </form>

            </td>

            <td>
            ₹{item["subtotal"]:.2f}
            </td>

            <td>

                <form
                    method="post"
                    action="/remove-from-cart"
                >

                    <input
                        type="hidden"
                        name="product_id"
                        value="{item["id"]}"
                    >

                    <button>
                    Remove
                    </button>

                </form>

            </td>

        </tr>

        """

    if not rows:

        rows = """
        <tr>
            <td colspan="5">
            Your cart is empty.
            </td>
        </tr>
        """

    checkout_button = ""

    if items:

        checkout_button = """

        <div class="total">
        Total: ₹{:.2f}
        </div>

        <a
            class="btn"
            href="/checkout"
        >
        Proceed to Checkout
        </a>

        """.format(total)

    content = f"""

    <h1>Shopping Cart</h1>

    <table>

        <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Subtotal</th>
            <th>Action</th>
        </tr>

        {rows}

    </table>

    {checkout_button}

    """

    return page("Cart", content)


# =========================================================
# UPDATE CART
# =========================================================

@app.route("/update-cart", methods=["POST"])
def update_cart():

    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    connection = get_db()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    if product and 1 <= quantity <= product["stock"]:

        cart = session.get("cart", {})

        cart[product_id] = quantity

        session["cart"] = cart

        flash("Cart updated.")

    else:

        flash("Invalid quantity.")

    return redirect(url_for("cart"))


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():

    product_id = request.form["product_id"]

    cart = session.get("cart", {})

    cart.pop(product_id, None)

    session["cart"] = cart

    flash("Product removed from cart.")

    return redirect(url_for("cart"))


# =========================================================
# CHECKOUT
# =========================================================

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():

    items, total = get_cart()

    if not items:

        flash("Your cart is empty.")

        return redirect(url_for("products"))

    if request.method == "POST":

        delivery_slot = request.form["delivery_slot"]
        payment_method = request.form["payment_method"]

        connection = get_db()

        cursor = connection.execute("""
            INSERT INTO orders
            (
                user_id,
                total,
                delivery_slot,
                payment_method,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            total,
            delivery_slot,
            payment_method,
            "Confirmed"
        ))

        order_id = cursor.lastrowid

        for item in items:

            connection.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    quantity,
                    price
                )
                VALUES (?, ?, ?, ?)
            """, (
                order_id,
                item["id"],
                item["quantity"],
                item["price"]
            ))

            connection.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                item["quantity"],
                item["id"]
            ))

        connection.commit()

        connection.close()

        session["cart"] = {}

        return redirect(
            url_for(
                "order_confirmation",
                order_id=order_id
            )
        )

    item_list = ""

    for item in items:

        item_list += f"""

        <li>
        {item["name"]}
        × {item["quantity"]}
        = ₹{item["subtotal"]:.2f}
        </li>

        """

    content = f"""

    <div class="form-box">

        <h2>Checkout</h2>

        <h3>Order Summary</h3>

        <ul>
        {item_list}
        </ul>

        <div class="total">
        Total: ₹{total:.2f}
        </div>

        <form method="post">

            <label>
            Delivery Slot
            </label>

            <select
                name="delivery_slot"
                required
            >

                <option value="">
                Select a delivery slot
                </option>

                <option>
                9:00 AM - 12:00 PM
                </option>

                <option>
                12:00 PM - 3:00 PM
                </option>

                <option>
                3:00 PM - 6:00 PM
                </option>

                <option>
                6:00 PM - 9:00 PM
                </option>

            </select>

            <label>
            Payment Method
            </label>

            <select
                name="payment_method"
                required
            >

                <option value="">
                Select payment method
                </option>

                <option>
                Cash on Delivery
                </option>

                <option>
                UPI
                </option>

                <option>
                Debit/Credit Card
                </option>

            </select>

            <button type="submit">
            Place Order
            </button>

        </form>

    </div>

    """

    return page("Checkout", content)


# =========================================================
# ORDER CONFIRMATION
# =========================================================

@app.route("/order-confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):

    connection = get_db()

    order = connection.execute("""
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        session["user_id"]
    )).fetchone()

    connection.close()

    if not order:

        flash("Order not found.")

        return redirect(url_for("products"))

    content = f"""

    <div class="hero">

        <h1>
        Order Confirmed!
        </h1>

        <p>
        Your grocery order has been successfully placed.
        </p>

        <h2>
        Order ID: #{order["id"]}
        </h2>

        <p>
        <b>Total:</b>
        ₹{order["total"]:.2f}
        </p>

        <p>
        <b>Delivery Slot:</b>
        {order["delivery_slot"]}
        </p>

        <p>
        <b>Payment:</b>
        {order["payment_method"]}
        </p>

        <p>
        <b>Status:</b>
        {order["status"]}
        </p>

        <br>

        <a
            class="btn"
            href="/orders"
        >
        View My Orders
        </a>

    </div>

    """

    return page(
        "Order Confirmation",
        content
    )


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/orders")
@login_required
def orders():

    connection = get_db()

    orders_list = connection.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    rows = ""

    for order in orders_list:

        rows += f"""

        <tr>

            <td>
            #{order["id"]}
            </td>

            <td>
            ₹{order["total"]:.2f}
            </td>

            <td>
            {order["delivery_slot"]}
            </td>

            <td>
            {order["payment_method"]}
            </td>

            <td>
            {order["status"]}
            </td>

        </tr>

        """

    if not rows:

        rows = """

        <tr>

            <td colspan="5">
            No orders found.
            </td>

        </tr>

        """

    content = f"""

    <h1>My Orders</h1>

    <table>

        <tr>

            <th>Order ID</th>
            <th>Total</th>
            <th>Delivery Slot</th>
            <th>Payment</th>
            <th>Status</th>

        </tr>

        {rows}

    </table>

    """

    return page("My Orders", content)


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    initialize_database()

    print("---------------------------------------")
    print(" Grocery Delivery Application")
    print(" Developed by Praveen Kumar")
    print("---------------------------------------")
    print("Open: http://127.0.0.1:5000")

    app.run(debug=True)
