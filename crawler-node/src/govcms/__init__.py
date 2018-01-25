'''
the APPROXIMATE_SAAS_LIST is our best estimate of the sites hosted on
govCMS SaaS. We should replace this with a govCMS detector.
'''
import re
from bs4 import BeautifulSoup

# Use this list to "seed" the list of known govCMS sites.
# It was reasonably correct not long before this file was created,
# but will of course rot over time.
APPROXIMATE_SAAS_LIST = [
    'agedcare.health.gov.au', 'www.anao.gov.a', 'www.amr.gov.au',
    'www.army.gov.au', 'www.arts.gov.au', 'annualreport.ato.gov.au',
    'www.agd.sa.gov.au', 'www.anzacatt.org.au', 'www.abcc.gov.au',
    'www.aclei.gov.au', 'www.acic.gov.au', 'www.acorn.gov.au',
    'www.afsa.gov.au', 'www.arpansa.gov.au', 'www.asada.gov.au',
    'www.aviationcomplaints.gov.au', 'beta.ato.gov.au',
    'campaigns.health.gov.au', 'www.casa.gov.au', 'www.cdpp.gov.au',
    'www.cert.gov.au', 'blog.data.gov.au', 'www.mhs.gov.au',
    'www.defencecommunityhub.org.au', 'www.minister.defence.gov.au',
    'www.childprotection.sa.gov.au', 'www.communications.gov.au',
    'www.fpwhitepaper.gov.au', 'www.electioncostings.gov.au',
    'esta.vic.gov.au', 'www.eex.gov.au', 'www.energy.gov.au',
    'measures.environment.gov.au', 'www.govcms.gov.au',
    'support.govdex.gov.au', 'www.domainname.gov.au',
    'www.icacreviewer.sa.gov.au', 'www.ihpa.gov.au',
    'www.ipaustralia.gov.au', 'migrationblog.border.gov.au',
    'www.nca.gov.au', 'nccgr.govspace.gov.au', 'www.nfsa.gov.au',
    'www.nwfc.gov.au', 'www.ona.gov.au', 'outnback.casa.gov.au',
    'www.ppsr.gov.au', 'postentryquarantine.govspace.gov.au',
    'poweringforward.energy.gov.au', 'providertoolkit.ndis.gov.au',
    'www.psr.gov.au', 'innovation.govspace.gov.au',
    'www.childabuseroyalcommission.gov.au', 'www.decd.sa.gov.au',
    'skillselect.govspace.gov.au', 'soe.environment.gov.au',
    'statistical-data-integration.govspace.gov.au',
    'www.staysmartonline.gov.au', 'www.teqsa.gov.au',
    'www.asqa.gov.au', 'www.ttipattorney.gov.au',
    'www.budget.vic.gov.au'
]

# If an HTML page has this meta tag in it's <head/>, then it is appears
# to be generated with an instance of the GovCMS software
# <meta
#     name="generator"
#     content="Drupal 7 (http://drupal.org) + govCMS (http://govcms.gov.au)"
# />
#
# presumably, one day this will change (to Drupal 8?). When it does, our
# we will probably want to change this to a list of known values...
GOVCMS_HTML_HEAD_META_GENERATOR = "Drupal 7 (http://drupal.org) + govCMS (http://govcms.gov.au)"

# If an HTML page has a <script> in the <head>, and the body of the script
# matches this RegExe, we assume it is running on the Australian government's
# instance of govCMS. That's because all govCMS sites are linked into the the same
# whole-of-government google analytics service
#
# if this changes, it will look likst all the govCMS hosted sites suddenly
# stopped being hosted by govCMS. I.e. the detector will blow up;
GOVCMS_HEAD_SCRIPT_REGEX = "UA-54970022-1"
ga_regex = re.compile(GOVCMS_HEAD_SCRIPT_REGEX)


def looks_like_govCMS_html(text):
    '''
    Returns a number representing how much this html looks like
    it comes from the Australian Government's drupal govCMS

    * -1 unable to parse as html
    * 0 html, but unlike we expect from govCMS
    * 1 somewhat govCMS-like
    * 2 more govCMS-like
    '''
    # can parse as HTML?
    try:
        soup = BeautifulSoup(text, 'html.parser')
    except Exception as e:
        print(e)
        return -1

    score = 0

    # has the "meta-generator" feature
    if soup.meta:
        generator_meta = {
            "name": "generator",
            "content": GOVCMS_HTML_HEAD_META_GENERATOR
        }
        if soup.head.find_all('meta', attrs=generator_meta):
            score += 1

    # no point matching more than once
    ga_regex_seen = False

    # has a script ga strings?
    for script in soup.find_all('script'):
        code = script.text
        if code:
            if not ga_regex_seen:
                matches = ga_regex.search(code)
                if matches:
                    ga_regex_seen = True
                    score += 1
    return score
