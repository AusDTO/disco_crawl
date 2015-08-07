//First version just send hosts

//Get host list
//apply changes (csv?) - Get from data.gov.au too?

//upload new data
// http --json POST http://demo.ckan.org/api/3/action/resource_update id=<resource id>
// upload=@updated_file.csv
// Authorization:<api key>

var Promise = require('bluebird');

var logger = require('./config/logger');
var conf = require('./config/config');
var crawlDb = require('./lib/ormCrawlDb');
var request = require('request');

logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance) + '\n');

//Add an extra database function to fetch the host list and mark duplicates

crawlDb.getHosts = function() {
  orm = this;
  return new Promise(function(resolve, reject) {
    orm.db.query('SELECT host FROM "webDocuments" WHERE "httpCode" < 300 GROUP BY host;').spread(function(results, metadata) {
      results = results.sort();
      // Results will be an array and metadata will contain the number of affected rows
      results.forEach(function(item, index, array) {
        //          console.log(item.host);
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


crawlDb.connect()
  .then(
    function() {
      console.log('do');
      crawlDb.getHosts()
        .then(function(results) {
          var resultString = 'HOST,DUPLICATE\n';
          results.forEach(function(result) {
            resultString += result.host + ',' + (result.duplicate === true).toString() + '\n';
          });
//          console.log(resultString);

request('http://demo.ckan.org/api/3/action/resource_update', funcstion (error, response, body) {
  if (!error && response.statusCode == 200) {
    console.log(body) // Show the HTML for the Google homepage.
  }
})


          // https://data.gov.au/api/3/action/resource_update?id=08557cab-df37-45b1-9f19-5f85efcf05bd/resource/1e44826f-ae14-40ad-b7e2-125dc82a36bd/download/test.csv
          //http --json POST http://demo.ckan.org/api/3/action/resource_update id=1e44826f-ae14-40ad-b7e2-125dc82a36bd
          // upload=@updated_file.csv
          // Authorization:<api key>

        });
    })
  .catch(function(e) {
    logger.error(e);
  });
