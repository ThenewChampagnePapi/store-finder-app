from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from urllib.parse import quote_plus
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- Model -----------------
class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    city = db.Column(db.String(64))
    state = db.Column(db.String(32))
    address = db.Column(db.String(200))
    # Per-store search URL template using {query} placeholder
    search_template = db.Column(db.String(300))  # e.g., https://www.bestbuy.com/site/searchpage.jsp?st={query}

    def location_str(self):
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        return self.city or self.state or "—"

# -------------- Auto-migrate (SQLite) --------------
with app.app_context():
    db.create_all()
    try:
        cols = [r[1] for r in db.session.execute(text("PRAGMA table_info(store)"))]
        if "address" not in cols:
            db.session.execute(text("ALTER TABLE store ADD COLUMN address VARCHAR(200)"))
        if "search_template" not in cols:
            db.session.execute(text("ALTER TABLE store ADD COLUMN search_template VARCHAR(300)"))
        db.session.commit()
    except Exception as e:
        print("Auto-migrate note:", e)

# ----------------- Routes -----------------
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

        # Optional: capture template at creation if provided
        example_url = (request.form.get("example_url") or "").strip()
        sample_item = (request.form.get("sample_item") or "").strip()
        search_template = None
        if example_url and sample_item:
            if sample_item in example_url:
                search_template = example_url.replace(sample_item, "{query}", 1)
            else:
                flash("If you provide an example URL, it must include the sample item text.", "error")

        if not name:
            flash("Store name is required.", "error")
            return render_template("store_new.html",
                                   form={"name": name, "city": city, "address": address, "state": state,
                                         "example_url": example_url, "sample_item": sample_item})

        s = Store(
            name=name,
            city=city or None,
            state=state or None,
            address=address or None,
            search_template=search_template
        )
        db.session.add(s)
        db.session.commit()
        flash("Store added!", "success")
        return redirect(url_for("store_detail", store_id=s.id))

    return render_template("store_new.html", form={})

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

# ---------- Save/update template FROM the store page ----------
@app.route("/stores/<int:store_id>/template", methods=["POST"])
def store_set_template(store_id):
    s = Store.query.get_or_404(store_id)
    example_url = (request.form.get("example_url") or "").strip()
    sample_item = (request.form.get("sample_item") or "").strip()

    if not example_url or not sample_item:
        flash("Both Example URL and Sample Item are required.", "error")
        return redirect(url_for("store_detail", store_id=s.id))
    if sample_item not in example_url:
        flash("Sample item text not found in the Example URL.", "error")
        return redirect(url_for("store_detail", store_id=s.id))

    s.search_template = example_url.replace(sample_item, "{query}", 1)
    db.session.commit()
    flash("Search template saved!", "success")
    return redirect(url_for("store_detail", store_id=s.id))

# ---------- Search FROM the store page ----------
@app.route("/stores/<int:store_id>/search", methods=["POST"])
def store_search(store_id):
    s = Store.query.get_or_404(store_id)
    item = (request.form.get("item") or "").strip()

    if not s.search_template:
        flash("No search template saved yet for this store. Save one below.", "error")
        return redirect(url_for("store_detail", store_id=s.id))
    if not item:
        flash("Please enter an item to search for.", "error")
        return redirect(url_for("store_detail", store_id=s.id))

    # Replace {query} with the user's item (URL-encoded)
    url = s.search_template.replace("{query}", quote_plus(item))
    return redirect(url)

if __name__ == "__main__":
    app.run(debug=True)
