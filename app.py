from flask import Flask, render_template

app = Flask(__name__)

stores = [
    {"id": 1, "name": "Costco", "location": "Omaha, NE", "url": "https://www.costco.com/warehouse-locations/omaha-ne-1012.html"},
    {"id": 2, "name": "Target", "location": "Papillion, NE", "url": "https://www.target.com/sl/omaha/2125"},
    {"id": 3, "name": "Best Buy", "location": "La Vista, NE", "url": "https://stores.bestbuy.com/ne/omaha/333-n-170th-st-240.html"},
]

@app.route("/")
def home():
    return render_template("index.html", stores=stores)

@app.route("/store/<int:store_id>")
def store_detail(store_id):
    store = next((s for s in stores if s["id"] == store_id), None)
    return render_template("store.html", store=store)

if __name__ == "__main__":
    print("Flask is starting...")
    app.run(debug=True)
