var http = require('http');
var Promise = require('bluebird');
var request = Promise.promisify(require('request'));
var logger = require('./config/logger');
var conf = require('./config/config');
var crawlDb = require('./lib/ormCrawlDb');
var moment = require('moment');
var join = Promise.join;
var apiKey = require('./config/apiKey');

logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance) + '\n');


var dgaOutputUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/1e44826f-ae14-40ad-b7e2-125dc82a36bd/download/hosts.csv';
var dgaBlacklistUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/6239de78-b28c-45a8-add2-413ed6a6f88a/download/blacklist.csv';
var dgaWhitelistUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/8aea9d2f-fd21-42ef-8cc5-bf9db3533bf8/download/whitelist.csv';

function buildHostdata(existingHosts, blackList, whitelist) {
  //

  crawlDb.connect()
  .then(
    function() {
      logger.debug('do');
      crawlDb.getHosts()
        .then(function(results) {
          var resultString = 'HOST,DUPLICATE\n';
          results.forEach(function(result) {
            resultString += result.host + ',' + (result.duplicate === true).toString() + '\n';
          });
          request('http://demo.ckan.org/api/3/action/resource_update', function(error, response, body) {
            if (!error && response.statusCode == 200) {
              logger.debug(body); // Show the HTML for the Google homepage.
            }
          });
        });
    })
  .catch(function(e) {
    logger.error(e);
  });
}



//Add an extra database function to fetch the host list and mark duplicates
crawlDb.getHosts = function() {
  orm = this;
  return new Promise(function(resolve, reject) {
    orm.db.query('SELECT host, min("httpCode") FROM "webDocuments" GROUP BY host;').spread(function(results, metadata) {
      results = results.sort();
      // Results will be an array and metadata will contain the number of affected rows
      results.forEach(function(item, index, array) {
        //          logger.debug(item.host);
        if (item.host.search('^www\.') >= 0) {
          var duplicateSearch = item.host.slice(4);
          var duplicateSet = array.filter(function(row) {
            return row.host === duplicateSearch;
          });

          if (duplicateSet.length > 0) {
            item.duplicate = true;
          } else {
            item.duplicate = false;
          }
        } else {
          item.duplicate = false;
        }
      });
      resolve(results);
    });
  });
};

function shouldJobRun(lastOutputUpdate, lastBlacklistUpdate, lastWhitelistUpdate) {
  if (lastOutputUpdate.isBefore(moment().subtract(7, 'days'))) {
    logger.debug('output > 7 days old');
    return true;
  } else if (
    lastBlacklistUpdate.isAfter(lastOutputUpdate) ||
    lastWhitelistUpdate.isAfter(lastOutputUpdate)) {
    logger.debug('whitelist/blacklist newer than output');
    return true;
  }
  return false;
}

function getResource(options) {
  return new Promise(function(resolve, reject) {

    request({
        url: options.url,
        headers: {
          'Authorization': options.apiKey
        }
      })
      .spread(function(response, body) {
        logger.debug('Getting ' + options.name);

        resolve({
          name: options.name,
          response: response,
          body: body
        });
      })
      .catch(function(err) {
        logger.error(err);
      });
  });
}


join(getResource({
    name: 'output',
    url: 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/1e44826f-ae14-40ad-b7e2-125dc82a36bd/download/hosts.csv',
    apiKey: apiKey
  }), getResource({
    name: 'blacklist',
    url: 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/6239de78-b28c-45a8-add2-413ed6a6f88a/download/blacklist.csv',
    apiKey: apiKey
  }), getResource({
    name: 'whitelist',
    url: 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/8aea9d2f-fd21-42ef-8cc5-bf9db3533bf8/download/whitelist.csv',
    apiKey: apiKey
  }),
  function(outputResponse, blacklistResponse, whitelistResponse) {
    logger.debug('output: ' + outputResponse.body);
    logger.debug('Joining');
    logger.debug('blacklist: ' + blacklistResponse.body);
    logger.debug('whitelist: ' + whitelistResponse.body);

    var lastOutputUpdate = moment(new Date(outputResponse.response.headers['last-modified'])); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastBlacklistUpdate = moment(new Date(blacklistResponse.response.headers['last-modified'])); //, 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastWhitelistUpdate = moment(new Date(whitelistResponse.response.headers['last-modified'])); // 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    logger.debug('Dates... \noutput:  \t' + lastOutputUpdate.format() + ' \nblacklist:\t' + lastBlacklistUpdate.format() + '\nwhitelist:\t' + lastWhitelistUpdate.format());


    if (shouldJobRun(lastOutputUpdate, lastBlacklistUpdate, lastWhitelistUpdate)) {
      logger.debug('Updating Host Data');


    } else {
      logger.debug('No Update Required');
    }

  });
