#Overview
This appplication crawls all gov.au domaians (excluding states and territories) and stores the resouces
found in a database. It is the intent that other components of the discovery layer will then modify and
enhane that crawled information to support an improved user experience.

It is a node application largely based on the simplecrawler projecct and orientDb.

##Options
There are a large set of options available to control the crawler behaviour. These can be altered through environment variables or as command line parameters. Refer to the config/config.js file for information.

##Significant Internal Functions

###Crawl Control
#### Timeout
This function allow the application to only run for a specific time. Once completed any resources that have not
been fetched are persisted to be selected later.

#### Fetch Condition - gov.au domain restriction
Ensures that we only follow links to Australian Government Domains (not state)

#### Fetch Condition - Max items Processed
No items are processed above the max items limit, they are instead persisted to the database to be fetched another time.

#### Fetch Condition - Only Fetch If Due
Items are not processed if the next Fetch data has not been reached.

#### Fetch Condition - Exclude Domains
Processes the set of regex patterns set in the config/excludedDomains.txt. If matched to the host, the item will not be fetched.

#### Fetch Condition - Exclude Urls
Processes the set of regex patterns set in the config/excludedUrls.txt. If matched to the full url, the item will not be fetched.

### newQueueList
Fetches a list of items that are ready to be fetched from the database. Note the orderFlip option will get the list ordered in the opposite order.

###addIfMissing
Stores an item in the database if not already there. Used when deffering tasks.

###upSert
Update or Insert. If item is missing it will insert otherwise it will create a copy delete and insert.

###checkNextFetchDate
Gets and checks the next fetch date in the database ccompared to todays date.

###buildWebDocument
Builds the object to be inserted in the database based on the simplecrawler queueItem

###queueUrl
Override of the simplecrawler function to allow checking the database if the item is ready to fetch.

#Docker

TODO - Add some docker information
