#Overview
This application crawls all gov.au domains (excluding states and territories) and stores the resources
found in a database. It is the intent that this information be used for a wide variety of applications which require an understanding across government.
Analytics, search and alternative content presentations have already been considered in this context.

These applications are intended to be implemented as part of other projects but may reuse the outputs of this project.

>#Access
>We are very open to creative use of the data created through this crawling exercise. If you would like access to the information/database feel free to contact us through an issue and we will do what we can to assist.

##Technical Information
It is a dockerised node application largely based on the simplecrawler project integrated with a postgres database using sequelize to provide object relational mapping. For more information on the node packages used, refer to the package.json file.

> Note: The queueUrl method of the simplecrawler has been overridden to allow easy integration with promise based database methods.

The crawl was initiated from a seed list of domains (located in config/seedDomains.txt) which was obtained from the domain registrar, this was loaded using the queueitems script.

The process selects a set (the size of which is configurable) of urls, fetches the content and parses it for any urls to other content. Once processed, the content and related header information is stored in the database and a date to refetch the content is set. This process continues for a configured set of time or number of fetched resources, the urls of any resources that are outstanding after this time are also stored in the database to allow them to be retrieved in the next iteration of the process.

Regex rules can be set to exclude resources based on either a host or full url pattern match. These rules are applied through the lib/crawlRules script which references the excludedDomains.txt and excludedUrls.txt files.

The crawler does not currently respect robot files.

##Options
There are a large set of options available to control the crawler behavior. These can be altered through environment variables or as command line parameters. Refer to the config/config.js file for information.
