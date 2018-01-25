'''
the APPROXIMATE_SAAS_LIST is our best estimate of the sites hosted on
govCMS SaaS. We should replace this with a govCMS detector.
'''
import unittest
from govcms import looks_like_govCMS_html

class GovCMSTestCase(unittest.TestCase):

    def test_govcms_detector(self):
        with open("govcms/sample.html", 'r') as fp:
            score = looks_like_govCMS_html(fp)
        self.assertEqual(score, 2)

if __name__ == "__main__":
    unittest.main()
