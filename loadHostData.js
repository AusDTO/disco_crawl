var fs = require('fs');
var http = require('http');
var Promise = require('bluebird');
var request = Promise.promisify(require('request'));
var logger = require('./config/logger');
var conf = require('./config/config');
var crawlDb = require('./lib/ormCrawlDb');
var moment = require('moment');
var csvParse = require('csv');
var json2csv = require('json2csv');

var join = Promise.join;
var apiKey = require('./config/apiKey');

logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance) + '\n');


crawlDb.getHosts = function() {
  orm = this;
  return new Promise(function(resolve, reject) {
    orm.db.query('SELECT host, min("httpCode") as "minHttpCode" FROM "webDocuments" GROUP BY host;').spread(function(results, metadata) {
      //results = results.sort();
      //logger.debug('DB response: ' + JSON.stringify(results));
      logger.debug('DB metadata: ' + JSON.stringify(metadata));
      // Results will be an array and metadata will contain the number of affected rows
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
        logger.debug('Result: ' + body);
        csvParse.parse(body, {
          columns: true,
          skip_empty_lines: true
        }, function(err, objectBody) {
          console.log(objectBody);
          resolve({
            name: options.name,
            response: response,
            body: objectBody
          });
        });

      })
      .catch(function(err) {
        logger.error(err);
      });
  });
}

function buildHostdata(existingHosts, newHosts, blacklist, whitelist) {
  return new Promise(function(resolve, reject) {
    newHosts.forEach(function(host) {
      host.whitelisted = false;
      host.blacklisted = false;
      host.wwwduplicate = false;
      if (host.minHttpCode < 300) {
        host.servescontent = true;
      } else {
        host.servescontent = false;
      }
      blacklist.forEach(function(blacklistHost) {
        if (host.host === blacklistHost.host) {
          host.blacklisted = true;
          logger.debug('blacklisting: ' + JSON.stringify(host));
        }
      });
    });
    whitelist.forEach(function(whitelistHost) {
      whitelistHost = {
        host: whitelistHost.host,
        whitelisted: true,
        blacklisted: false,
        minHttpCode: null,
        wwwduplicate: false,
        servescontent: null
      };
      logger.debug('whitelisting: ' + JSON.stringify(whitelistHost));
      newHosts.push(whitelistHost);
    });
    var deduplicateddHosts = [];
    newHosts.forEach(function(item, index, array) {
      if (item.host) {
        //logger.debug('DB row: ' + JSON.stringify(item));
        if (item.host.search('^www\.') >= 0) {
          var duplicateSearch = item.host.slice(4);
          var duplicateSet = array.filter(function(row) {
            return row.host === duplicateSearch;
          });

          if (duplicateSet.length > 0) {
            item.wwwduplicate = true;
            //logger.debug('Duplicate host: ' + item.host);
          }
        }
        //logger.debug(JSON.stringify(item) + '-----' + deduplicateddHosts.length);
        deduplicateddHosts.push(item);
    //TODO: servingcontent is not being set correctly
    //TODO: Should not need to do this redundant copy
    //TODO: Compare old and new before uploading. That might be a diff function
      }
    });

    //logger.debug('Final Result... \n' + JSON.stringify(newHosts, null, 2));
    resolve(deduplicateddHosts);
  });
}

function createCsv(hostsDataObject) {
  return new Promise(function(resolve, reject) {
    json2csv({
      data: hostsDataObject
    }, function(err, csv) {
      if (err) {
        logger.debug('err: ' + err);
        reject(err);
      }
      //logger.debug('csv' + csv);
      resolve(csv);
    });
  });
}



//do a promise join to request/query each resource in parallel and process when all promises resolve.
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
  crawlDb.getHosts(),
  function(outputResponse, blacklistResponse, whitelistResponse, newHosts) {
    //logger.debug('output: ' + outputResponse.body);
    logger.debug('Joining');
    //logger.debug('blacklist: ' + blacklistResponse.body);
    //logger.debug('whitelist: ' + whitelistResponse.body);

    var lastOutputUpdate = moment(new Date(outputResponse.response.headers['last-modified'])); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastBlacklistUpdate = moment(new Date(blacklistResponse.response.headers['last-modified'])); //, 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastWhitelistUpdate = moment(new Date(whitelistResponse.response.headers['last-modified'])); // 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    logger.debug('Dates... \noutput:  \t' + lastOutputUpdate.format() + ' \nblacklist:\t' + lastBlacklistUpdate.format() + '\nwhitelist:\t' + lastWhitelistUpdate.format());

    if (shouldJobRun(lastOutputUpdate, lastBlacklistUpdate, lastWhitelistUpdate) || conf.get('debug') === true) {
      buildHostdata(outputResponse.body, newHosts, blacklistResponse.body, whitelistResponse.body)
        .then(function(hostDataObject) {
          createCsv(hostDataObject)
            .then(function(csvString) {
              fs.writeFile('hosts.csv', csvString);
              //sendCsv(csvString);
            })
            .catch(function(e) {
              logger.error(e);
            });
        })
        .catch(function(e) {
          logger.error(e);
        });
      logger.debug('Updating Host Data');
    } else {
      logger.debug('No Update Required');
    }

  });
