"""ShopLab — web app đích của nhóm cho RQ3/RQ4: đăng nhập, sản phẩm, giỏ hàng, checkout, hồ sơ.

    python apps/shoplab/app.py --variant v0 --port 5100

Mọi id/label/text/hành vi đọc từ `variants.config(variant)` để tạo mutation có kiểm soát.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, session, url_for

sys.path.insert(0, str(Path(__file__).parent))
from variants import VARIANTS, config  # noqa: E402

USERS = {"alice": ("secret123", False), "bob": ("secret123", True)}  # (mật khẩu, bị khoá)
PRODUCTS = [("backpack", "Sauce Backpack", 2999), ("bike-light", "Bike Light", 999), ("t-shirt", "Bolt T-Shirt", 1599)]
PRICE = {slug: cents for slug, _, cents in PRODUCTS}
NAME = {slug: name for slug, name, _ in PRODUCTS}

LAYOUT = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ShopLab</title>
<style>body{font-family:sans-serif;max-width:720px;margin:24px auto}nav a{margin-right:12px}
.card{border:1px solid #ccc;padding:8px;margin:8px 0}.error{color:#b00}.ok{color:#070}</style></head><body>
{% if session.get('user') %}<nav><a href="/products">Products</a>
<a href="/cart">{{c.cart_link}} (<span data-testid="{{c.badge_testid}}" id="cart-count">{{ session.get('cart', [])|length + (1 if c.badge_bug else 0) }}</span>)</a>
<a href="/profile">Profile</a><a href="/logout">{{c.logout_link}}</a></nav>{% endif %}
{{ body|safe }}</body></html>"""

LOGIN = """<h1>ShopLab</h1>
{% if msg %}<div id="flash" role="status" class="ok">{{msg}}</div>{% endif %}
<form method="post" action="/login">
{% if c.wrap %}<div class="field-wrap"><div class="inner">{% endif %}
<label for="{{c.user_id}}">{{c.user_label}}</label>
<input id="{{c.user_id}}" name="username" placeholder="{{c.user_ph}}" data-testid="{{c.user_testid}}">
{% if c.wrap %}</div></div>{% endif %}
<label for="{{c.pass_id}}">{{c.pass_label}}</label>
<input id="{{c.pass_id}}" name="password" type="password" placeholder="{{c.pass_ph}}" data-testid="{{c.pass_testid}}">
<button id="{{c.login_btn_id}}" type="submit">{{c.login_btn}}</button>
</form>
{% if error %}<div id="{{c.error_id}}" role="alert" class="error">{{error}}</div>{% endif %}"""

PRODUCTS_T = """<h1>Products</h1>
{% for slug, name, cents in products %}<div class="card{% if c.wrap %} product-card{% endif %}">
<h2>{{name}}</h2><span class="{{c.price_class}}">${{ '%.2f' % ((cents - (1000 if c.price_bug and loop.first else 0))/100) }}</span>
<form method="post" action="/add/{{slug}}" style="display:inline">
<button data-testid="{{ c.add_testid.format(slug=slug) }}" aria-label="{{c.add_btn}} {{name}}">{{c.add_btn}}</button></form>
</div>{% endfor %}"""

CART = """<h1>Your Cart</h1>
{% for slug in items %}<div class="cart-item">{{ names[slug] }}</div>{% else %}<p>Cart is empty</p>{% endfor %}
<p class="{{c.total_class}}" id="total">Total: ${{ '%.2f' % (total/100) }}</p>
<a href="/checkout" role="button">{{c.checkout_btn}}</a>"""

CHECKOUT = """<h1>Checkout</h1>
<form method="post" action="/checkout">
<label for="first">{{c.first_label}}</label><input id="first" name="first">
<label for="last">{{c.last_label}}</label><input id="last" name="last">
<label for="zip">{{c.zip_label}}</label><input id="zip" name="zip">
<button type="submit">{{c.continue_btn}}</button></form>
{% if error %}<div id="{{c.error_id}}" role="alert" class="error">{{error}}</div>{% endif %}"""

PROFILE = """<h1>Profile</h1>
<form method="post" action="/profile">
<label for="display-name">{{c.name_label}}</label><input id="display-name" name="name" value="{{name}}">
<button type="submit">{{c.save_btn}}</button></form>
{% if saved %}<div id="message" role="status" class="{{ 'error' if c.save_fails else 'ok' }}">{{ c.msg_save_failed if c.save_fails else c.msg_saved }}</div>{% endif %}"""


def create_app(variant: str = "v0") -> Flask:
    c = config(variant)
    app = Flask(__name__)
    app.secret_key = f"shoplab-{variant}"

    def page(tpl: str, **kw):
        return render_template_string(LAYOUT, c=c, body=render_template_string(tpl, c=c, **kw))

    def need_login():
        return None if session.get("user") else redirect(url_for("login"))

    @app.get("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return page(LOGIN, msg=c["msg_logout"] if request.args.get("bye") else None, error=None)
        user, pw = request.form.get("username", "").strip(), request.form.get("password", "")
        if not user:
            return page(LOGIN, msg=None, error=c["msg_required"])
        if user not in USERS or USERS[user][0] != pw:
            return page(LOGIN, msg=None, error=c["msg_invalid"])
        if USERS[user][1] and not c["locked_allowed"]:
            return page(LOGIN, msg=None, error=c["msg_locked"])
        session.clear()
        session["user"], session["cart"] = user, []
        return redirect(c["after_login"])

    @app.get("/logout")
    def logout():
        if c["logout_noop"]:
            return redirect(url_for("products"))
        session.clear()
        return redirect("/login?bye=1")

    @app.get("/products")
    def products():
        return need_login() or page(PRODUCTS_T, products=PRODUCTS)

    @app.post("/add/<slug>")
    def add(slug):
        if (r := need_login()) is not None:
            return r
        if slug in PRICE and not c["add_noop"]:
            session["cart"] = session.get("cart", []) + [slug]
        return redirect(url_for("products"))

    @app.get("/cart")
    def cart():
        if (r := need_login()) is not None:
            return r
        items = session.get("cart", [])
        counted = items[1:] if c["total_bug"] else items
        return page(CART, items=items, names=NAME, total=sum(PRICE[s] for s in counted))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        if (r := need_login()) is not None:
            return r
        if request.method == "GET":
            return page(CHECKOUT, error=None)
        if not request.form.get("first", "").strip() and not c["skip_first_validation"]:
            return page(CHECKOUT, error=c["msg_first_required"])
        session["cart"] = []
        return redirect(url_for("complete"))

    @app.get("/complete")
    def complete():
        return need_login() or page(f"<h1>{c['thanks']}</h1>")

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        if (r := need_login()) is not None:
            return r
        if request.method == "POST" and not c["save_fails"]:
            session["name"] = request.form.get("name", "")
        return page(PROFILE, name=session.get("name", session["user"]), saved=request.method == "POST")

    return app


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="v0", choices=list(VARIANTS))
    ap.add_argument("--port", type=int, default=5100)
    args = ap.parse_args()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    create_app(args.variant).run(host="127.0.0.1", port=args.port, threaded=True)
