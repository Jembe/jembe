from jembe import Component

def test_simple_page(jmb, client):
    class SimplePage(Component):
        pass
    
    jmb.add_page("simple_page", SimplePage)
    r = client.get("/simple_page")
    assert r.status_code == 200
    assert b'<h1>Simple page</h1>' in r.data 
    assert b'<html lang="en" jmb:name="/simple_page" jmb:data="{}"' in r.data 

def test_empty_page(jmb, client):
    class EmptyPage(Component):
        def display(self):
            return self.render_template_string("")
    
    jmb.add_page("page", EmptyPage)
    r = client.get("/page")
    assert r.status_code == 200
    assert b'<html jmb:name="/page" jmb:data="{}">' in r.data 
    assert b'<div></div>' in r.data 
