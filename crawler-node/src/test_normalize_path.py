#!/usr/bin/env python
from worker import normalize_href, urlparse

data = [
    ('/a/b/c/', 'a.txt'),
    ('/a/b/c/', 'b/'),
    ('/a/b/c/', '../../uew.txt'),
    ('/a/b/c/', '..'),
    ('/a/b/c/', '/subdirinc/'),
    ('/', 'index.html'),
    ('', 'index.html'),
    ('', ''),
    ('https://wow.org/a/b/c/', '/absolute/'),
    ('https://wow.org/a/b/c/', 'http://external.domain/first-url#xx'),
    ('https://wow.org/a/b/c/', '#somestuff'),
    ('https://wow.org/a/b/c/', '?get=parameter'),
    ('/a/b/c/', 'a.txt'),
    ('', '/subdirinc/'),
    ('#fragment', '/absolute/'),
]

for d1, d2 in data:
    print(d1, d2, normalize_href(d2, urlparse(d1)))
