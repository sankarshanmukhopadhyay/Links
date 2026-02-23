from links.utils import summarize

def test_summarize_empty():
    assert summarize([]) == "empty"

def test_summarize_nonempty():
    assert summarize([1, 2, 3]) == "3 items, first=1"
