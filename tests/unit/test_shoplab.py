"""ShopLab (app đích RQ3/RQ4) + tổng hợp số đo RQ3 — offline qua Flask test client, không cần trình duyệt."""
from apps.shoplab.app import create_app
from apps.shoplab.suite import load_suite, with_base
from apps.shoplab.variants import VARIANTS
from run_rq3 import summarize


def _client(variant):
    return create_app(variant).test_client()


def _login(c, user="alice", pw="secret123"):
    return c.post("/login", data={"username": user, "password": pw})


def test_every_variant_labelled():
    kinds = {v["kind"] for name, v in VARIANTS.items() if name != "v0"}
    assert kinds == {"technical", "semantic"}


def test_v0_business_rules():
    c = _client("v0")
    assert _login(c).headers["Location"].endswith("/products")
    assert b"Account is locked" in _login(_client("v0"), "bob").data
    c.post("/add/backpack")
    c.post("/add/bike-light")
    assert b"Total: $39.98" in c.get("/cart").data
    assert b"First name is required" in c.post("/checkout", data={"first": "", "last": "N", "zip": "1"}).data


def test_semantic_mutations_change_behaviour():
    assert b"Account is locked" not in _login(_client("S5_locked"), "bob").data
    assert _login(_client("S4_redirect")).headers["Location"].endswith("/profile")
    c = _client("S2_total")
    _login(c)
    c.post("/add/backpack")
    c.post("/add/bike-light")
    assert b"Total: $39.98" not in c.get("/cart").data


def test_technical_mutation_keeps_behaviour_changes_ui():
    c = _client("T4_login_text")
    page = c.get("/login").data
    assert b"Sign in" in page and b">Login<" not in page
    assert _login(c).headers["Location"].endswith("/products")


def test_suite_base_substitution():
    tc, plan = load_suite()[0]
    assert plan.actions[0].arg == "{BASE}/login"
    assert with_base(plan, "http://x").actions[0].arg == "http://x/login"


def test_summarize_masking_and_weakening():
    rows = [
        {"arm": "a", "kind": "technical", "variant": "T1", "outcome": "repaired", "weakened": False},
        {"arm": "a", "kind": "technical", "variant": "T1", "outcome": "repaired", "weakened": True},
        {"arm": "a", "kind": "semantic", "variant": "S1", "outcome": "repaired", "weakened": True},
        {"arm": "a", "kind": "semantic", "variant": "S1", "outcome": "escalated"},
    ]
    s = summarize(rows, ["a"])["a"]
    assert (s["tech_repaired"], s["tech_repaired_any"], s["sem_masked"], s["escalated"], s["weakened"]) == (1, 2, 1, 1, 2)
