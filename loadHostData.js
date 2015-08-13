var fs = require('fs');
var Promise = require('bluebird');
var request = Promise.promisify(require('request'));
var moment = require('moment');
var ckan = require('ckan');
var logger = require('./config/logger');
var conf = require('./config/config');
var crawlDb = require('./lib/ormCrawlDb');
var hostTools = require('./lib/hostTools');
var apiKey = require('./config/apiKey');
var csvParse = require('csv');
var join = Promise.join;
var client = new ckan.Client('http://data.gov.au', conf.get('apiKey'));

logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance) + '\n');


crawlDb.getHosts = function() {
  orm = this;
  return new Promise(function(resolve, reject) {
    orm.db.query('SELECT host, min("httpCode") as "minHttpCode" FROM "webDocuments" GROUP BY host;').spread(function(results, metadata) {
      //results = results.sort();
      //logger.debug('DB response: ' + JSON.stringify(results));
      //logger.debug('DB metadata: ' + JSON.stringify(metadata));
      // Results will be an array and metadata will contain the number of affected rows
      resolve(results);
      //TODO: remove null hosts through HAVING?
    });
  });
};

function getResource(options) {
  return new Promise(function(resolve, reject) {
    //TODO: remove null hosts
    //TODO: Add call to resource info to get updated date.
    // client.action('resource_show', {id: '377bc789-63ec-4cc0-9d2a-987f26d7a521'}, function(err, result) {
    //   logger.debug(JSON.stringify(result));
    // });
    client.action('datastore_search', {
      resource_id: options.resource_id
    }, function(err, result) {
      logger.debug('Getting ' + options.name);
      if (!err) {
        logger.debug('Result: ' + JSON.stringify(result.result.records));
        resolve({
          name: options.name,
          response: result.result.records,
        });
      } else {
        logger.error(err);
      }
    });
  });
}



//TODO: Setup apiKey and resource ids.

var baseDataUrl = 'https://data.gov.au/api/action/datastore_search?resource_id=';
//TODO: Replace gets with action api
join(
  getResource({
    name: 'blacklist',
    resource_id: conf.get('whitelistId'),
    apiKey: conf.get('apiKey')
  }), getResource({
    name: 'whitelist',
    resource_id: conf.get('blacklistId'),
    apiKey: conf.get('apiKey')
  }),
  crawlDb.getHosts(),

  function(blacklistResponse, whitelistResponse, newHosts) {
    logger.debug('Joining');

    // var lastOutputUpdate = moment(new Date(outputResponse.response.headers['last-modified'])); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    // var lastBlacklistUpdate = moment(new Date(blacklistResponse.response.headers['last-modified'])); //, 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    // var lastWhitelistUpdate = moment(new Date(whitelistResponse.response.headers['last-modified'])); // 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT

    //    logger.info('Dates... \noutput:  \t' + lastOutputUpdate.format() + ' \nblacklist:\t' + lastBlacklistUpdate.format() + '\nwhitelist:\t' + lastWhitelistUpdate.format());
    // client.action('resource_show', {id: '377bc789-63ec-4cc0-9d2a-987f26d7a521'}, function(err, result) {
    //   logger.debug(JSON.stringify(result));
    // });

    // if (hostTools.shouldJobRun(lastOutputUpdate, lastBlacklistUpdate, lastWhitelistUpdate) || conf.get('debug') === true) {
    //   logger.info('Updating Host Data');

    hostTools.buildHostdata(null, newHosts, blacklistResponse.response, whitelistResponse.response)
      .then(function(hostDataObject) {
        fs.writeFile('hosts.json', JSON.stringify(hostDataObject));
        client.action('datastore_delete', {
          resource_id: conf.get('outputId'),
          force: true
        }, function(err, response) {
          client.action('datastore_create', {
              resource_id: conf.get('outputId'),
              last_modified: moment().format('YYYY-MM-DD'),
              fields: [{
                'id': 'host',
                'type': 'text'
              }, {
                'id': 'whitelisted',
                'type': 'bool'
              }, {
                'id': 'blacklisted',
                'type': 'bool'
              }, {
                'id': 'wwwduplicate',
                'type': 'bool'
              }, {
                'id': 'servescontent',
                'type': 'bool'
              }],
              force: true,
              records: hostDataObject
            },
            function(err, resource) {
              if (!err) {
                logger.info("Resource Updated");
              } else {
                logger.error("Resource NOT Updated: " + err);
                logger.error("More: " + JSON.stringify(resource));
              }
            });
        });
      })
      .catch(function(e) {
        logger.error(e);
      });
    // } else {
    //   logger.info('No Update Required');
    //   process.exit();
    //}

  });
