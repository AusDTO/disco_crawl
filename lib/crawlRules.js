var fs = require('fs');
var nodeURL = require('url');
var logger = require('../config/logger');
var path = require('path');
var conf = require('../config/config');

var temp = fs.readFileSync('./config/excludedDomains.txt').toString().split("\n");
var domainRegex = [];
temp.forEach(function(rule) {
  if (rule.length > 0) {
    domainRegex.push(new RegExp(rule));
  }
});

temp = fs.readFileSync('./config/excludedUrls.txt').toString().split("\n");
var urlRegex = [];
temp.forEach(function(rule) {
  if (rule.length > 0) {
    urlRegex.push(new RegExp(rule));
  }

});

var maxitems = conf.get('maxItems');

//NOTE: This should only be used for testing purposes. It is not accurate becuase it doesnt account for fetched/unfetched

//TODO: Make sure maxitems is checked before adding condition
//var maxItems = conf.get('maxItems');


module.exports = {


  commDomain: function(parsedURL) {
    var stateRegex =  /(^|\.)vic\.gov\.au$|(^|\.)nsw\.gov\.au$|(^|\.)qld\.gov\.au$|(^|\.)tas\.gov\.au$|(^|\.)act\.gov\.au$|(^|\.)sa\.gov\.au$|(^|\.)wa\.gov\.au$|(^|\.)nt\.gov\.au$/;
    if (parsedURL.host.substring(parsedURL.host.length - 7) == ".gov.au") {
      if (parsedURL.host.search(stateRegex) < 0) {
        return true;
      } else {
        logger.debug("State Domain Encountered: " + parsedURL.host); //a state
        return false;
      }
    } else {
      logger.debug("Non gov.au Domain: " + parsedURL.host); //non gov au
      return false; //not gov.au
    }
  },
  notExcludedDomain: function(parsedURL, crawler) {

    for (var i = 0; i < domainRegex.length; i++) {
      if (parsedURL.host.search(domainRegex[i]) >= 0) {
        return false;
      }
    }
    return true;
  },

  notExcludedUrl: function(parsedURL, crawler) {
    //TODO: Actually want the full url here

    parsedURL.pathname = parsedURL.path;
    urlString = nodeURL.format(parsedURL);

    for (var i = 0; i < urlRegex.length; i++) {
      if (urlString.search(urlRegex[i]) >= 0) {
        return false;
      }
    }
    return true;
  },

  maxItems: function(parsedURL, crawler) {
    if (crawler.queue.length >= maxitems) {
      delete parsedURL.uriPath;
      parsedURL.pathname = parsedURL.path;
      var queueItem = parsedURL;
      queueItem.url = nodeURL.format(parsedURL);
      queueItem.status = 'deferred';
      crawler.emit("deferurl",queueItem);
      //crawlDb.addIfMissing(queueItem);
      logger.debug("URL Deferred (q=" + crawler.queue.length + "): " + queueItem.url);
      return false;
    } else {
      return true;
    }
  }

};
