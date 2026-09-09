from replora.retrieval import load_dataset, retrieve


def test_dataset_loads():
    data = load_dataset()
    assert len(data) >= 10
    assert all(x.incoming_email and x.reference_reply for x in data)


def test_billing_query_retrieves_billing_example():
    data = load_dataset()
    results = retrieve("I was charged twice for my subscription", data, top_k=3)
    assert results
    assert results[0].example.category == "billing"
