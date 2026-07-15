"""Thread namespacing helpers."""
from app.graph.runtime import make_thread_id, user_id_from_thread


def test_make_thread_id_namespaces():
    assert make_thread_id("demo-new", "abc") == "demo-new:abc"


def test_make_thread_id_idempotent():
    assert make_thread_id("demo-new", "demo-new:abc") == "demo-new:abc"


def test_make_thread_id_strips_other_user_prefix():
    assert make_thread_id("demo-new", "demo-veteran:abc") == "demo-new:abc"


def test_user_id_from_thread():
    assert user_id_from_thread("demo-veteran:weekly-review") == "demo-veteran"
