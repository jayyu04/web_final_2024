from app import app
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 用於 session 加密
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql://root:@127.0.0.1/project_silver"  # 更新為你的數據庫URI
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# 定義數據庫模型
class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    product_price = db.Column(db.Float, nullable=False)


class Order(db.Model):
    __tablename__ = "orderlist"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(150), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    product_amount = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=False)


@app.route("/")
def home():
    logged_in = "member_id" in session
    return render_template("home.html", logged_in=logged_in)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 這裡應該是你檢查使用者帳號和密碼的邏輯
        if username == "testuser" and password == "testpassword":
            session["member_id"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("member_id", None)
    return redirect(url_for("home"))


@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        member_id = request.form.get("member_id")
        product_id = request.form.get("product_id")
        order_date = datetime.strptime(request.form.get("order_date"), "%Y-%m-%d")
        product_amount = int(request.form.get("product_amount"))
        total_price = float(request.form.get("total_price"))

        new_order = Order(
            member_id=member_id,
            product_id=product_id,
            order_date=order_date,
            product_amount=product_amount,
            total_price=total_price,
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "failure", "error": str(e)})


@app.route("/admin")
def admin_page():
    orders = (
        db.session.query(Order, User, Product)
        .join(User, Order.member_id == User.member_id)
        .join(Product, Order.product_id == Product.product_id)
        .all()
    )
    return render_template("admin_page.html", orders=orders)


@app.route("/store")
def store():
    products = Product.query.all()
    member_id = session.get("member_id", None)
    return render_template("store.html", products=products, member_id=member_id)


@app.route("/register", methods=["GET", "POST"])
def member_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm-password"]
        name = request.form["name"]
        email = request.form["email"]
        address = request.form["address"]
        phone = request.form["phone"]

        if password != confirm_password:
            return jsonify("密碼和確認密碼不相符")

        # 在這裡你可以進行進一步的數據驗證和清理，以防止 SQL 注入等攻擊
        new_user = User(
            username=username,
            password=password,
            name=name,
            email=email,
            address=address,
            phone=phone,
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify("註冊成功")
        except Exception as e:
            db.session.rollback()
            return jsonify(f"註冊失敗: {str(e)}")

    return render_template("register.html")


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "member_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["member_id"])

    if request.method == "POST":
        user.username = request.form["username"]
        user.password = request.form["password"]
        user.name = request.form["name"]
        user.email = request.form["email"]
        user.address = request.form["address"]
        user.phone = request.form["phone"]

        try:
            db.session.commit()
            flash("資料已更新", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"更新失敗: {str(e)}", "danger")

        return redirect(url_for("edit_profile"))

    return render_template("edit_profile.html", user=user)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
