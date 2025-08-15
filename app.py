from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---- Model ----
class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    city = db.Column(db.String(64))
    state = db.Column(db.String(32))
    address = db.Column(db.String(200))

    def location_str(self):
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        return self.city or self.state or "—"

# ---- Ensure tables exist + add 'address' if missing (SQLite) ----
with app.app_context():
    db.create_all()
    try:
        cols = [r[1] for r in db.session.execute(text("PRAGMA table_info(store)"))]
        if "address" not in cols:
            db.session.execute(text("ALTER TABLE store ADD COLUMN address VARCHAR(200)"))
            db.session.commit()
    except Exception as e:
        print("Address auto-migrate check skipped:", e)

# ---- Routes ----
@app.route("/")
def home():
    stores = Store.query.order_by(Store.name.asc()).all()
    return render_template("index.html", stores=stores)

@app.route("/stores/<int:store_id>")
def store_detail(store_id):
    s = Store.query.get_or_404(store_id)
    return render_template("store_detail.html", store=s)

@app.route("/stores/new", methods=["GET", "POST"])
def store_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        city = (request.form.get("city") or "").strip()
        address = (request.form.get("address") or "").strip()
        state = (request.form.get("state") or "").strip()

        if not name:
            flash("Store name is required.", "error")
            return render_template("store_new.html",
                                   form={"name": name, "city": city, "address": address, "state": state})

        s = Store(name=name, city=city or None, address=address or None, state=state or None)
        db.session.add(s)
        db.session.commit()
        flash("Store added!", "success")
        return redirect(url_for("store_detail", store_id=s.id))

    return render_template("store_new.html", form={})

# ---- EDIT: accepts POST from detail page ----
@app.route("/stores/<int:store_id>/edit", methods=["POST"])
def store_edit(store_id):
    s = Store.query.get_or_404(store_id)

    name = (request.form.get("name") or "").strip()
    city = (request.form.get("city") or "").strip()
    address = (request.form.get("address") or "").strip()
    state = (request.form.get("state") or "").strip()

    if not name:
        flash("Store name is required.", "error")
        return redirect(url_for("store_detail", store_id=s.id))

    s.name = name
    s.city = city or None
    s.address = address or None
    s.state = state or None
    db.session.commit()

    flash("Store updated!", "success")
    return redirect(url_for("store_detail", store_id=s.id))

@app.route("/stores/<int:store_id>/delete", methods=["POST"])
def store_delete(store_id):
    s = Store.query.get_or_404(store_id)
    db.session.delete(s)
    db.session.commit()
    flash("Store deleted.", "success")
    return redirect(url_for("home"))

print("Loaded routes:")
for rule in app.url_map.iter_rules():
    print(rule, "->", rule.endpoint, "methods:", list(rule.methods))

if __name__ == "__main__":
    if not os.path.exists("app.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
