from datetime import date
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from .db import get_db
from .auth import login_required, owner_required

bp = Blueprint("shop", __name__)

def money(value):
    return f"{value:,.0f} RWF"

@bp.app_template_filter("rwf")
def rwf(value):
    return money(float(value or 0))

@bp.get("/")
@login_required
def dashboard():
    db = get_db()
    sales = db.execute("SELECT COALESCE(SUM(total_amount),0) total FROM sales WHERE date(sale_date)=date('now','localtime')").fetchone()["total"]
    products = db.execute("SELECT COUNT(*) total FROM products WHERE is_active=1").fetchone()["total"]
    stock_value = db.execute("SELECT COALESCE(SUM(quantity*buying_price),0) total FROM products WHERE is_active=1").fetchone()["total"]
    expenses = db.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE date(expense_date)=date('now','localtime')").fetchone()["total"]
    low = db.execute("SELECT * FROM products WHERE is_active=1 AND quantity<=low_stock_level ORDER BY quantity").fetchall()
    recent = db.execute("SELECT s.*,u.full_name FROM sales s JOIN users u ON u.id=s.user_id ORDER BY s.id DESC LIMIT 6").fetchall()
    return render_template("dashboard.html", sales=sales, products=products, stock_value=stock_value, expenses=expenses, low=low, recent=recent)

@bp.route("/products", methods=["GET","POST"])
@login_required
def products():
    db = get_db()
    if request.method == "POST":
        if g.user["role"] != "owner":
            flash("Only the Owner can add products.", "error")
            return redirect(url_for("shop.products"))
        name = request.form.get("name","").strip()
        category_id = request.form.get("category_id") or None
        try:
            buying = float(request.form.get("buying_price",""))
            selling = float(request.form.get("selling_price",""))
            qty = int(request.form.get("quantity","0"))
            low = int(request.form.get("low_stock_level","5"))
            if not name or buying < 0 or selling < 0 or qty < 0 or low < 0:
                raise ValueError()
            cur = db.execute("INSERT INTO products(name,category_id,buying_price,selling_price,quantity,low_stock_level) VALUES(?,?,?,?,?,?)",
                             (name,category_id,buying,selling,qty,low))
            if qty:
                db.execute("INSERT INTO stock_movements(product_id,user_id,movement_type,quantity_change,quantity_after,note) VALUES(?,?,'stock_in',?,?,?)",
                           (cur.lastrowid,g.user["id"],qty,qty,"Opening stock"))
            db.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("shop.products"))
        except (ValueError, TypeError):
            db.rollback()
            flash("Enter a valid name, prices and whole-number quantities.", "error")
    rows = db.execute("SELECT p.*,c.name category FROM products p LEFT JOIN categories c ON c.id=p.category_id WHERE p.is_active=1 ORDER BY p.name").fetchall()
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("products.html", products=rows, categories=cats)

@bp.post("/categories")
@owner_required
def add_category():
    name = request.form.get("name","").strip()
    if name:
        try:
            get_db().execute("INSERT INTO categories(name) VALUES(?)",(name,))
            get_db().commit()
            flash("Category added.", "success")
        except Exception:
            get_db().rollback()
            flash("That category may already exist.", "error")
    return redirect(url_for("shop.products"))

@bp.post("/products/<int:product_id>/stock")
@login_required
def stock_in(product_id):
    db = get_db()
    try:
        amount = int(request.form.get("amount",""))
        if amount <= 0:
            raise ValueError()
        product = db.execute("SELECT * FROM products WHERE id=? AND is_active=1",(product_id,)).fetchone()
        if product is None:
            flash("Product not found.", "error")
        else:
            after = product["quantity"] + amount
            db.execute("UPDATE products SET quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(after,product_id))
            db.execute("INSERT INTO stock_movements(product_id,user_id,movement_type,quantity_change,quantity_after,note) VALUES(?,?,'stock_in',?,?,?)",
                       (product_id,g.user["id"],amount,after,"Stock received"))
            db.commit()
            flash("Stock updated.", "success")
    except ValueError:
        db.rollback()
        flash("Enter a positive whole number.", "error")
    return redirect(url_for("shop.products"))

@bp.post("/products/<int:product_id>/deactivate")
@owner_required
def deactivate_product(product_id):
    db=get_db()
    db.execute("UPDATE products SET is_active=0 WHERE id=?",(product_id,))
    db.commit()
    flash("Product deactivated.", "success")
    return redirect(url_for("shop.products"))

@bp.route("/sales", methods=["GET","POST"])
@login_required
def sales():
    db=get_db()
    if request.method=="POST":
        try:
            product_ids=request.form.getlist("product_id")
            quantities=request.form.getlist("quantity")
            requested={}
            for pid,q in zip(product_ids,quantities):
                if not pid:
                    raise ValueError("Choose a product for every sale line.")
                qty=int(q)
                product_id=int(pid)
                if qty<=0:
                    raise ValueError("Quantities must be greater than zero.")
                requested[product_id]=requested.get(product_id,0)+qty

            lines=[]
            total=0.0
            for product_id,qty in requested.items():
                p=db.execute("SELECT * FROM products WHERE id=? AND is_active=1",(product_id,)).fetchone()
                if p is None or p["quantity"]<qty:
                    raise ValueError(f"Insufficient stock for {p['name'] if p else 'selected product'}.")
                line=qty*float(p["selling_price"])
                total+=line
                lines.append((p,qty,line))
            if not lines:
                raise ValueError("Add at least one item.")
            cur=db.execute("INSERT INTO sales(receipt_number,user_id,total_amount) VALUES(?,?,?)",
                           ("KB-"+uuid4().hex[:10].upper(),g.user["id"],total))
            sale_id=cur.lastrowid
            for p,qty,line in lines:
                db.execute("INSERT INTO sale_items(sale_id,product_id,product_name,quantity,unit_price,unit_cost,line_total) VALUES(?,?,?,?,?,?,?)",
                           (sale_id,p["id"],p["name"],qty,p["selling_price"],p["buying_price"],line))
                after=p["quantity"]-qty
                db.execute("UPDATE products SET quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(after,p["id"]))
                db.execute("INSERT INTO stock_movements(product_id,user_id,movement_type,quantity_change,quantity_after,note) VALUES(?,?,'sale',?,?,?)",
                           (p["id"],g.user["id"],-qty,after,f"Sale {sale_id}"))
            db.commit()
            flash(f"Sale completed. Total: {money(total)}","success")
            return redirect(url_for("shop.sales"))
        except (ValueError,TypeError) as exc:
            db.rollback()
            flash(str(exc) or "Please enter valid quantities.","error")
    products=db.execute("SELECT * FROM products WHERE is_active=1 AND quantity>0 ORDER BY name").fetchall()
    history=db.execute("SELECT s.*,u.full_name FROM sales s JOIN users u ON u.id=s.user_id ORDER BY s.id DESC LIMIT 30").fetchall()
    return render_template("sales.html",products=products,history=history)

@bp.route("/expenses", methods=["GET","POST"])
@login_required
def expenses():
    db=get_db()
    if request.method=="POST":
        try:
            title=request.form.get("title","").strip()
            category=request.form.get("category","").strip()
            amount=float(request.form.get("amount",""))
            notes=request.form.get("notes","").strip()
            if not title or not category or amount<=0:
                raise ValueError()
            db.execute("INSERT INTO expenses(title,category,amount,notes,recorded_by) VALUES(?,?,?,?,?)",
                       (title,category,amount,notes,g.user["id"]))
            db.commit()
            flash("Expense saved.","success")
            return redirect(url_for("shop.expenses"))
        except ValueError:
            db.rollback()
            flash("Enter a title, category and positive amount.","error")
    rows=db.execute("SELECT e.*,u.full_name FROM expenses e JOIN users u ON u.id=e.recorded_by ORDER BY e.id DESC LIMIT 100").fetchall()
    return render_template("expenses.html",expenses=rows)

@bp.get("/reports")
@owner_required
def reports():
    db=get_db()
    start=request.args.get("start") or date.today().replace(day=1).isoformat()
    end=request.args.get("end") or date.today().isoformat()
    sales_total=db.execute("SELECT COALESCE(SUM(total_amount),0) n FROM sales WHERE date(sale_date) BETWEEN ? AND ?",(start,end)).fetchone()["n"]
    cogs=db.execute("SELECT COALESCE(SUM(si.quantity*si.unit_cost),0) n FROM sale_items si JOIN sales s ON s.id=si.sale_id WHERE date(s.sale_date) BETWEEN ? AND ?",(start,end)).fetchone()["n"]
    expenses_total=db.execute("SELECT COALESCE(SUM(amount),0) n FROM expenses WHERE date(expense_date) BETWEEN ? AND ?",(start,end)).fetchone()["n"]
    return render_template("reports.html",start=start,end=end,sales_total=sales_total,cogs=cogs,expenses_total=expenses_total,gross=float(sales_total)-float(cogs),operating=float(sales_total)-float(cogs)-float(expenses_total))


@bp.post("/chatbot/reply")
@login_required
def chatbot_reply():
    """Answer common KoraBiz how-to questions without sending data outside the app."""
    message = request.get_json(silent=True) or {}
    question = str(message.get("message", "")).strip().lower()[:500]
    if not question:
        return jsonify({"reply": "Please type a question about using KoraBiz."}), 400

    answers = [
        (("add product", "new product", "create product"),
         "To add a product, open Products. Owners can fill in the product name, category, buying price, selling price, opening quantity and low-stock level, then select Add product."),
        (("stock", "restock", "add inventory", "inventory"),
         "Open Products & Inventory. Find the item, enter the quantity in its Stock in box, then select Add. The quantity must be a positive whole number."),
        (("make sale", "record sale", "sell", "sales"),
         "Open Sales, choose a product and quantity, then select Complete sale. KoraBiz calculates the total and reduces stock. A sale is rejected if there is not enough stock."),
        (("expense", "record expense", "add expense"),
         "Open Expenses. Enter the expense title, category, amount in RWF and optional notes, then select Save expense."),
        (("report", "profit", "gross profit", "operating result"),
         "Owners can open Reports and choose a date range. Gross profit is sales revenue minus cost of goods sold. Operating result also subtracts recorded expenses."),
        (("low stock", "low-stock", "alert"),
         "The dashboard lists active products whose quantity is at or below their low-stock level. You can add stock from the Products page."),
        (("attendant", "user account", "create user", "staff"),
         "An Owner can create an attendant account from the terminal with: python -m flask --app run.py create-attendant. The attendant can record sales, stock received and expenses, but cannot access Owner reports or add products."),
        (("login", "password", "sign in"),
         "Use the username and password created for your account on the login page. If you cannot sign in, ask the shop Owner to check that your account is active."),
        (("currency", "rwf", "franc"),
         "KoraBiz displays shop amounts in Rwandan francs (RWF). Enter prices and expenses as numbers; the system adds the RWF label."),
    ]
    for keywords, answer in answers:
        if any(word in question for word in keywords):
            return jsonify({"reply": answer})
    return jsonify({"reply": "I can help with products, stock, sales, expenses, reports, low-stock alerts, accounts and login. Try asking: 'How do I record a sale?'"})
