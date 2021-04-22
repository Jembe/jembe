from jembe.processor import EmitCommand

gmen = EmitCommand._glob_match_exec_name
"""
if pattern is:

    - None -> match to every initialised component 
    - /compoent1.key1/compoent2.key2    -> compoenent with complete exec_name
    - component                       -> match to direct child named "component" without key
    - component.*                     -> match to direct child named "component" with any key
    - component.key                   -> match to direct child named "component with key equals "key"
    - *                               -> match to any direct child
    - **/component[.[*|<key>]]        -> match to child at any level
    - ..                                -> match to parent
    - ../component[.[*|<key>]]          -> match to sibling 
    - /**/.                             -> match to parent at any level
    - /**/component[.[*|<key>]]/**/.    -> match to parent at any level named
    - etc.
"""


def test_match_any_component():
    sen = "/pa/ca/cb"
    pattern = None
    assert gmen(sen, pattern, "/pa/ca/cb")
    assert gmen(sen, pattern, "/pa/ca/cb.k2")
    assert gmen(sen, pattern, "/pa/ca/cb/cc")
    assert gmen(sen, pattern, "/pa/ca")
    assert gmen(sen, pattern, "/pb/cc")


def test_match_by_complete_name():
    sen = "/pa/ca/cb"
    assert gmen(sen, "/pa/ca/cb", "/pa/ca/cb")
    assert gmen(sen, "/pa/ca/cb", "/pa/ca/cb.k2") == False
    assert gmen(sen, "/pa/cc", "/pa/cc")
    assert gmen(sen, "/pa/cc.k1", "/pa/ca") == False
    assert gmen(sen, "/pb/cc.k1", "/pb/cc.k1")


def test_match_direct_chid_complete_name():
    sen = "/pa/ca"
    assert gmen(sen, "cb", "/pa/ca/cb")
    assert gmen(sen, "cb", "/pa/ca/cb.k1") == False
    assert gmen(sen, "cb.k1", "/pa/ca/cb") == False
    assert gmen(sen, "cb.k1", "/pa/ca/cb.k1")
    assert gmen(sen, "cb/cc", "/pa/ca/cb/cc")
    assert gmen(sen, "cb.k1/cc.k2", "/pa/ca/cb.k1/cc.k2")
    assert gmen(sen, "cb/cc", "/pa/ca/cb.k1/cc.k2") == False


def test_match_direct_chid_search_pattern():
    sen = "/pa/ca"
    assert gmen(sen, "cb.*", "/pa/ca/cb") == False
    assert gmen(sen, "cb.*", "/pa/ca/cb.k1") == True
    assert gmen(sen, "cb.*/cc.*", "/pa/ca/cb/cc") == False
    assert gmen(sen, "cb.*/cc.*", "/pa/ca/cb/cc.k2") == False
    assert gmen(sen, "cb.*/cc.*", "/pa/ca/cb.k1/cc.k2") == True
    assert gmen(sen, "cb.*/**/cc.*", "/pa/ca/cb.k1/cc.k2") == True
    assert gmen(sen, "cb.*/**/cc.*", "/pa/ca/cb.k1/cd/cc.k2") == True
    assert gmen(sen, "cb.*/**/cc.*", "/pa/ca/cb.k1/cd.kd/cc.k2") == True


def test_match_go_back_seach_pattern():
    sen = "/pa/ca"
    assert gmen(sen, "..", "/pa")
    assert gmen(sen, "../../pb/cb.*", "/pb/cb.k1")
    assert gmen(sen, "../cb.*/cc.*", "/pa/cb/cc") == False
    assert gmen(sen, "../cb.*/cc.*", "/pa/cb.k1/cc") == False
    assert gmen(sen, "../cb.*/cc.*", "/pa/cb.k1/cc.k2")
    assert gmen(sen, "../**/cb.*/cc.*", "/pa/cb.k1/cc.k2")
    assert gmen(sen, "../**/cb.*/cc.*", "/pa/cd/ck.kk/cb.k1/cc.k2")


def test_match_parrent_seach_pattern():
    sen = "/pa/ca/cb/cc/cd"
    assert gmen(sen, "/**/.", "/pa/ca/cb")
    assert gmen(sen, "/**/.", "/pa/ca")
    assert gmen(sen, "/**/.", "/pa/ca/cb/cc")
    assert gmen(sen, "/**/.", "/pb/ca/cb/cc") == False
    assert gmen(sen, "/**/cb/**/.", "/pa/ca/cb")
    sen = "/pa/ca/cb.k1/cc/cd"
    assert gmen(sen, "/**/cb.k1/**/.", "/pa/ca.ka/cb.k1") == False
    assert gmen(sen, "/**/cb.k1/**/.", "/pa/ca/cb.k1")
    sen = "/pa/ca/cb.k1/cc/cd"
    assert gmen(sen, "/**/cb.*/**/.", "/pa/ca/cb.k1")


def test_match_children():
    assert gmen("/pa/ca", "*", "/pa/ca/cb")
    assert gmen("/pa/ca", "*", "/pa/ca/cb.kb")
    assert gmen("/pa/ca", "*", "/pa/ca/cb.kb/cc") == False
    assert gmen("/pa/ca", "*.*", "/pa/ca/cb") == False
    assert gmen("/pa/ca", "*.*", "/pa/ca/cb.kb")
    assert gmen("/pa/ca", "*.*", "/pa/ca/cb.kb/cc") == False
    assert gmen("/pa/ca", "**/*", "/pa/ca/cb")
    assert gmen("/pa/ca", "**/*", "/pa/ca/cb/cc")
    assert gmen("/pa/ca", "**/*", "/pa/ca/cb.kb/cc")
    assert gmen("/pa/ca", "**/*", "/pa/ca/cb.kb/cc.kc")
    assert gmen("/pa/ca", "**/*.*", "/pa/ca/cb") == False
    assert gmen("/pa/ca", "**/*.*", "/pa/ca/cb/cc") == False
    assert gmen("/pa/ca", "**/*.*", "/pa/ca/cb.kb/cc") == False
    assert gmen("/pa/ca", "**/*.*", "/pa/ca/cb.kb/cc.kc")
    assert gmen("/pa/ca", "**/*.*", "/pa/ca/cb/cc.kc")
