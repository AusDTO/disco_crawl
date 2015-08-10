//First version just send hosts

//Get host list
//apply changes (csv?) - Get from data.gov.au too?

//upload new data
// http --json POST http://demo.ckan.org/api/3/action/resource_update id=<resource id>
// upload=@updated_file.csv
// Authorization:<api key>

//TODO: Run every 10 min.
//TODO: Pull blacklist, whitelist, current output
//TODO: if blacklist or whitelist "Last-Modified" header is after output "Last-Modified" header OR if output "Last-Modified" header is greater than 7 days old then process job.

var http = require('http');
var Promise = require('bluebird');
var request = Promise.promisify(require('request'));
var logger = require('./config/logger');
var conf = require('./config/config');
var crawlDb = require('./lib/ormCrawlDb');

var moment = require('moment');
var join = Promise.join;

logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance) + '\n');

//TODO: Move to conf
//var dgaOutputUrl = 'http://data.gov.au/api/3/action/resource_show?id=6239de78-b28c-45a8-add2-413ed6a6f88a';


//http http://demo.ckan.org/api/3/action/group_list id=data-explorer
var apiKey = '8224c7fd-a8eb-4660-bc55-73a81d609119';
var dgaOutputUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/1e44826f-ae14-40ad-b7e2-125dc82a36bd/download/hosts.csv';
var dgaBlacklistUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/6239de78-b28c-45a8-add2-413ed6a6f88a/download/blacklist.csv';
var dgaWhitelistUrl = 'https://data.gov.au/dataset/08557cab-df37-45b1-9f19-5f85efcf05bd/resource/8aea9d2f-fd21-42ef-8cc5-bf9db3533bf8/download/whitelist.csv';


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
    logger.debug('Joining');
    logger.debug('output: ' + outputResponse.body);
    logger.debug('blacklist: ' + blacklistResponse.body);
    logger.debug('whitelist: ' + whitelistResponse.body);

    var lastOutputUpdate = moment(new Date(outputResponse.response.headers['last-modified'])); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastBlacklistUpdate = moment(new Date(blacklistResponse.response.headers['last-modified'])); //, 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var lastWhitelistUpdate = moment(new Date(whitelistResponse.response.headers['last-modified'])); // 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
    var runJob;

    if (lastOutputUpdate.isBefore(moment().subtract(7, 'days'))) {
      runJob = true;
      logger.debug('output > 7 days old');
    } else if (
      lastBlacklistUpdate.isAfter(lastOutputUpdate) ||
      lastWhitelistUpdate.isAfter(lastOutputUpdate)) {
      logger.debug('whitelist/blacklist newer than output');
      runJob = true;
    }
    if (runJob) {
      logger.debug('Job should run');
    } else {
      logger.debug('Job should NOT run');
    }


  });









//TODO: Now do all the resouces
// var dgaOutput = body;
// var lastOutputUpdate = moment(new Date(response.headers['last-modified'])); //Format: Tue, 04 Aug 2015 15:20:58 GMT
// logger.debug('Output date: ' + response.headers['last-modified']);
// options.url = dgaBlacklistUrl;
// request.getAsync(options)
//   .then(function(error, response, body) {
//     if (!error && response.statusCode == 200) {
//       var dgaBlacklist = body;
//       var lastBlacklistUpdate = moment(new Date(response.headers['last-modified'])); //, 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
//       logger.debug('Blacklist date: ' + response.headers['last-modified']);
//       options.url = dgaWhitelistUrl;
//       request.getAsync(options)
//         .then(function(error, response, body) {
//           if (!error && response.statusCode == 200) {
//             var dgaWhitelist = body;
//             var lastWhitelistUpdate = moment(new Date(response.headers['last-modified'])); // 'ddd, DD MMM YYYY HH:MM:SS ZZZ'); //Format: Tue, 04 Aug 2015 15:20:58 GMT
//             logger.debug('Whitelist date: ' + response.headers['last-modified']);
//
//
//             logger.debug('Current Output Document: \n' + dgaOutput);
//             logger.debug('Current whitelist Document: \n' + dgaWhitelist);
//             logger.debug('Current blacklist Document: \n' + dgaBlacklist);
//
//             logger.debug('lastWhitelistUpdate: \t' + lastWhitelistUpdate.format());
//             logger.debug('lastBlacklistUpdate: \t' + lastBlacklistUpdate.format());
//             logger.debug('lastOutputUpdate: \t' + lastOutputUpdate.format());
//             runJob = false;
//             if (lastOutputUpdate.isBefore(moment().subtract(7, 'days'))) {
//               runJob = true;
//               logger.debug('output > 7 days old');
//             } else if (
//               lastBlacklistUpdate.isAfter(lastOutputUpdate) ||
//               lastWhitelistUpdate.isAfter(lastOutputUpdate)) {
//               logger.debug('whitelist/blacklist newer than output');
//               runJob = true;
//             }
//             if (runJob) {
//               logger.debug('Job should run');
//               logger.debug('Job should run');
//             } else {
//               logger.debug('Job should NOT run');
//             }
//           }
//         });
//     } //if
//   });
//    } //if
//});


//a thing to make sure all the requests are done (events/promises)
/*

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
          //          logger.debug(resultString);

          request('http://demo.ckan.org/api/3/action/resource_update', function(error, response, body) {
            if (!error && response.statusCode == 200) {
              logger.debug(body); // Show the HTML for the Google homepage.
            }
          });


          // https://data.gov.au/api/3/action/resource_update?id=08557cab-df37-45b1-9f19-5f85efcf05bd/resource/1e44826f-ae14-40ad-b7e2-125dc82a36bd/download/test.csv
          //http --json POST http://demo.ckan.org/api/3/action/resource_update id=1e44826f-ae14-40ad-b7e2-125dc82a36bd
          // upload=@updated_file.csv
          // Authorization:<api key>

        });
    })
  .catch(function(e) {
    logger.error(e);
  });

  */
