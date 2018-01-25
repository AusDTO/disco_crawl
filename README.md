# Overview
This application crawls all gov.au domains (excluding states and territories) and stores the resources
found in a index. It is the intent that this information be used for a wide variety of applications which require an understanding across government.
Analytics, search and alternative content presentations have already been considered in this context.

This was first started in 2015 but was not actively pursued or developed for a few years until late 2017. At this point the crawler was redeveloped for more effective horizontal scaling. This also meant moving from node to python in order to leverage functionality developed elsewhere.

The previous version is maintained in the archive-2015 branch.

># Access
>We are very open to creative use of the data created through this crawling exercise. If you would like access to the information/database feel free to contact us through an issue and we will do what we can to assist.

# Architectural Components
These are the basic components of the crawler architecture.
* Crawled pages storage: S3
* Parsed results storage: Elastic (ElasticSearch)
* Crawlers: EC2 boxes with access to S3 and SQS
* Redis database to hold:
  * seen domains
  * finished domains
  * currently locked domains

## Solution Overview
There is a single instance of a "steward" (crawlers-steward) which tasks crawler nodes (crawler-node) by putting the next domain url to an SQS queue.


### Steward Function

* selects website to crawl (based on Redis database)
* puts that website domain name to the requests queue


### Crawler Node Function
Each crawler node:
* Gets messages from the SQS
* Starts crawler process for that website, while being quite polite
* Ensures all required locks are set (so only single crawler downloads any domain name)
* Starts another crawler process for up to N websites (per single worker)
* For each new crawled page - put it's content to S3 and put the parsed metadata to Elastic

The saved metadata consists of:

* Source URL
* List of external HTTP links from this page
* List of external domains
* List of internal links, normalised ('a/b/../..' -> '/' and so on)
* Short text for search (summarized page content, not the whole page), keywords
* Http response details (time taken, status code, content metadata, etc)
* Other business data

Workers on each EC2 node may be scaled up until they keep the box busy (take 70-90% of memory). The limiting factor is a memory here.

### The Result
So, after some time, we have a lot of:

* data in our S3 bucket
* SQS messages spent
* Elastic records created


# Devops Information
The current proposed installation workflow relies on AWS, but it may be easily updated to any other devops environment.

Requirements:
* Elasticsearch service started and URL is available
* SQS queue created
  * we have IAM access key/secret to access it
  * we know the queue ARN
* Some EC2 boxes created:
  * one for steward
  * multiple (at least single) for crawlers
  * we have the SSH access to it

### Starting the crawlers
1. Deploy crawler-node to the target EC2 box
2. `cp prod-crawler-node.env.sample webindex-crawler-node.env` (if you rename that file make sure `docker-compose.yml` file `env_file` variable contains the valid value)
3. `docker-compose up` to start the crawler in sync mode (logs are shown, Control-C kills it)
   * `docker-compose up -d` to start it in the background (no logs shown directly and exit from the shell won't stop it)
   * `docker-compose up -d --scale crawler=10` to run 10 instancess
   * `docker-compose down` to stop/drop all instances
   * `docker-compose up -d --scale crawler=5` to tune instances count while they are running already
   * `docker-compose up -d --build` if you just have changed the source code (otherwise old one will be used)
   * `docker-compose logs --tail=40 -f` to see the logs from the containers

Usually you may start crawlers number to use 70% of the memory after a hour or two of crawlers working (experimental value). If you start too many they would kill the EC2 box, if too few - instance won't be used enough.

Experimental values: 20-25 crawlers per 8GB of the memory.

### Starting the steward
Works exactly the same as crawler instance, just .env file named differenently. Please ensure that both env files (from the crawler and from the steward) point to the same objects (SQS queue, redis instance and databases IDs).

### Creating a fleet
1. Run the steward
2. Set up single EC2 box with crawler and make sure it works fine for several hours - crawls data, doesn't use excessive memory (>90%) and so on
3. Go to AWS EC2 console and create a snapshot of that crawler Ec2 box
4. Create a spot request with given snapshot AMI, instance type: the same as source EC2 box, number: start from 3-5, everything else: default
5. Submit that spot request, wait for some time for instances to be provisioned and ensure Kibana has more data being crawled.

## Backups part
The following should be backed up:
* Elastic database
* S3 bucket
* Redis database content (mostly 'seen domains')
