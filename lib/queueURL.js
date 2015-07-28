var logger=require('../config/logger');
var crawlDb = require('./ormCrawlDb').get();
var nodeURL = require('url');


queueUrl = function(url,queueItem) {
	logger.debug("Queue URL input URL: " + JSON.stringify(url));
	//build a url string
	url.pathname = url.path;
            urlString = nodeURL.format(url);
            logger.debug("Converted URL: " + urlString);
	var crawler = this;
	var parsedURL =
		typeof(url) === "object" ? url : crawler.processURL(url,queueItem);

	// URL Parser decided this URL was junky. Next please!
	if (!parsedURL) {
		return false;
	}

	// Pass this URL past fetch conditions to ensure the user thinks it's valid
	var fetchDenied = false;
	fetchDenied = crawler._fetchConditions.reduce(function(prev,callback) {
		return prev || !callback(parsedURL);
	},false);
	
	if (fetchDenied) {
		//console.log('!!!Fetch Denied!!!' + url);
		// Fetch Conditions conspired to block URL
		return false;
	} else {
		//Check local queue
		if ( crawler.queue.scanIndex[url] ) {
		//allready queued, nothing to do
//		crawler.queue.exists(parsedURL.protocol, parsedURL.domain, parsedURL.port, parsedURL.path, function(err,exists){
			logger.debug('!!!Fetch Denied In Local Queue!!!' + urlString);
			return false;
		} else {
			//not queued locally check database
			logger.debug("Using URL: " + JSON.stringify(url) + " to check if ready");
			crawlDb.readyForFetch(urlString)
			.then(function(result){
				if(!result) { 
					//not ready for refetch so just bail
					logger.debug("Rejected URL: " + urlString + " becuase It was not ready to be refetched");
					return false;
					//TODO: Could add to local queue???
				}
				else {
					// Check the domain is valid before adding it to the queue
					if (crawler.domainValid(parsedURL.host)) {
						crawler.queue.add(
							parsedURL.protocol,
							parsedURL.host,
							parsedURL.port,
							parsedURL.path,
							parsedURL.depth,
							function queueAddCallback(error,newQueueItem) {
								if (error) {
									// We received an error condition when adding the callback
									if (error.code && error.code === "DUP")
										return crawler.emit("queueduplicate",parsedURL);

									return crawler.emit("queueerror",error,parsedURL);
								}

								crawler.emit("queueadd",newQueueItem,parsedURL);
								newQueueItem.referrer = queueItem ? queueItem.url : null;
							}
						);
					}
					return true;
				}
			}); //end ready for fetch

		}//end if exists
	} //end fetch denied

}

module.exports = queueUrl;