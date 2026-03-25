"""
Landing Page Renderer
=====================
Rendert Jinja2-Templates zu HTML-Dateien.
Lädt dynamische Texte aus dem Creative Agent (creatives.json).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    BRAND_NAME, WEBSITE_DOMAIN, GA4_MEASUREMENT_ID, META_PIXEL_ID,
    PRICE_ENTRY_PRODUCT, PRICE_UPSELL_PRODUCT
)

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "rendered_pages"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"])
)


def load_creatives() -> dict:
    """Lädt generierte Texte aus dem Creative Agent."""
    path = Path(__file__).parent.parent.parent / "data" / "creatives.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_base_context() -> dict:
    """Basis-Kontext für alle Pages."""
    return {
        "brand_name": BRAND_NAME,
        "website_domain": WEBSITE_DOMAIN,
        "ga4_id": GA4_MEASUREMENT_ID,
        "meta_pixel_id": META_PIXEL_ID,
        "entry_price": int(PRICE_ENTRY_PRODUCT),
        "upsell_price": int(PRICE_UPSELL_PRODUCT),
        "current_year": datetime.now().year,
    }


def render_optin(variant: str = "default") -> str:
    """Rendert die Opt-in Page."""
    creatives = load_creatives()
    lp_copy = creatives.get("landing_pages", {}).get("optin", {})

    context = get_base_context()
    context.update({
        "headline": lp_copy.get("headline", ""),
        "subheadline": lp_copy.get("subheadline", ""),
        "bullets": lp_copy.get("bullets", []),
        "cta_text": lp_copy.get("cta_text", "Jetzt kostenlos herunterladen →"),
        "form_action": f"https://{WEBSITE_DOMAIN}/danke",
        "variant": variant,
    })

    html = env.get_template("optin.html").render(**context)
    _save(html, f"optin_{variant}.html")
    return html


def render_thankyou(email: str = "") -> str:
    """Rendert die Danke-Seite."""
    context = get_base_context()
    context.update({
        "email": email,
        "sales_page_url": f"https://{WEBSITE_DOMAIN}/uc-ernaehrungs-kompass",
    })
    html = env.get_template("thankyou.html").render(**context)
    _save(html, "thankyou.html")
    return html


def render_sales(variant: str = "default") -> str:
    """Rendert die Sales Page."""
    creatives = load_creatives()
    lp_copy = creatives.get("landing_pages", {}).get("sales", {})

    context = get_base_context()
    context.update({
        "headline": lp_copy.get("headline", ""),
        "subheadline": lp_copy.get("subheadline", ""),
        "problems": lp_copy.get("problems", []),
        "benefits": lp_copy.get("benefits", []),
        "testimonials": lp_copy.get("testimonials", []),
        "faqs": lp_copy.get("faqs", []),
        "checkout_url": lp_copy.get("checkout_url", "#"),
        "variant": variant,
    })

    html = env.get_template("sales.html").render(**context)
    _save(html, f"sales_{variant}.html")
    return html


def render_upsell(variant: str = "default") -> str:
    """Rendert die Upsell Page."""
    creatives = load_creatives()
    lp_copy = creatives.get("landing_pages", {}).get("upsell", {})

    context = get_base_context()
    context.update({
        "upsell_headline": lp_copy.get("upsell_headline", ""),
        "upsell_subheadline": lp_copy.get("upsell_subheadline", ""),
        "modules": lp_copy.get("modules", []),
        "upsell_checkout_url": lp_copy.get("upsell_checkout_url", "#"),
        "thank_you_url": f"https://{WEBSITE_DOMAIN}/vielen-dank",
        "variant": variant,
    })

    html = env.get_template("upsell.html").render(**context)
    _save(html, f"upsell_{variant}.html")
    return html


def render_all():
    """Rendert alle Landing Pages."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendere Landing Pages nach: {OUTPUT_DIR}")

    render_optin()
    print("  ✓ optin.html")
    render_thankyou()
    print("  ✓ thankyou.html")
    render_sales()
    print("  ✓ sales.html")
    render_upsell()
    print("  ✓ upsell.html")

    print(f"\nAlle Pages gerendert → {OUTPUT_DIR}")


def _save(html: str, filename: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    render_all()
