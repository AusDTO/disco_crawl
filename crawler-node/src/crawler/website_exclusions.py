"""
Website-specific list of exclusions links
Format: dict with key = domain regexp, value = list of regexps of blacklisted links.
example:
{
    'humanservices.gov.au': [
        '/admin/.*',  # all starting from /admin/
        '*\.pdf$',  # anything ending with `.pdf`
    ],
    '.*': [ # any domain name
        'tel:.*'
    ]
}
"""

EXCLUDE = {
    '.*': [
        'tel:.*',
    ],
}
