def test_hello(client):
    response = client.get("/hello")
    assert response.data == b"Hello, World!"

def test_simple_page(client):
    response = client.get("/simple_page")
    assert response.status_code == 200
    assert b'<h1>Simple page</h1>' in response.data 
