# govCMS module

govCMS is a distribution of the drupal content management system, specifcally developed for running government web sites.

It is also the name of a service (which uses that drupal distribution) that hosts a significant proportion of Australian government web sites. See https://www.govcms.gov.au for more information about that.

Note there are two "versions" of the govCMS service:
 * "PaaS", the platform service used to host customised govCMS instances
 * "SaaS", a non-customised "software as a service" that is used by government sites that don't require custom features.

this govcms module contains some utility code:
 * "a govCMS detector"; given an HTML page, does it look like it came from govCMS?
 * some utility code that helps us treat all govcms sites as the same logical site, for the purpose of applying throttle limits.

This is important because our "broad and shallow" crawling strategy is designed to be polite; it is supposed to spread load thinly over the sites that we crawl. This does not have the intended effect in the case of govCMS hosted sites, because shared infrastructure is hosting a large number of the sites that we might be crawling in parallel.

The solution is to treat the collection of govcms sites as a single site, in a way that allows us to apply throttles to the collection, as well as applying them to individual sites. To do that, we need to maintain a list of govCMS sites (that's why the need a govCMS detector).
