from flask import Blueprint, render_template, request, flash, redirect, url_for

from app.utils.api_client import api_get, GatewayUnavailable, SessionExpired

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    search_term = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    products, categories = [], []
    try:
        if search_term or category:
            params = {}
            if search_term:
                params["q"] = search_term
            if category:
                params["category"] = category
            resp = api_get("/search", params=params)
        else:
            resp = api_get("/products")
        if resp.status_code == 200:
            products = resp.json()
        else:
            flash("The product catalog is temporarily unavailable. Please try again shortly.", "warning")

        cat_resp = api_get("/search/categories")
        if cat_resp.status_code == 200:
            categories = cat_resp.json()
    except GatewayUnavailable:
        flash("Unable to reach the catalog right now. Please try again shortly.", "danger")
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        search_term=search_term,
        selected_category=category,
    )


@main_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    try:
        resp = api_get(f"/products/{product_id}")
    except GatewayUnavailable:
        flash("Unable to reach the catalog right now.", "danger")
        return redirect(url_for("main.home"))
    except SessionExpired:
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if resp.status_code == 404:
        flash("Product not found.", "warning")
        return redirect(url_for("main.home"))

    return render_template("product_detail.html", product=resp.json())