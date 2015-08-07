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


logger.info('CrawlJob Settings: ' + JSON.stringify(conf._instance));

crawlDb.connect()
  .then(
    function() {
      console.log('do');
      crawlDb.getHosts()
        .then(function(results) {
            console.log(JSON.stringify(results, null, 3));
          });
        })
    .catch(function(e) {
      logger.error(e);
    });
