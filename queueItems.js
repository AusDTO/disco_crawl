var fs = require('fs');
var readline = require('readline');
var crawlDb = require('./lib/ormCrawlDb');
var winston = require('winston');

winston.add(winston.transports.File, {
  filename: './logs/queueItems.log'
});

crawlDb.connect()
  .then(function(crawlDb) {

    var count = 0;

    var rd = readline.createInterface({
      input: fs.createReadStream('./config/seedDomains.txt'),
      output: process.stdout,
      terminal: false
    });



    rd.on('line', function(line) {
        count++;
        item = {};
        item.url = "http://" + line + "/";
        //winston.info("Added : " + JSON.stringify(item));
        crawlDb.addIfMissing(item)
          .then(function(result, newRow) {
            winston.info("Added: " + JSON.stringify(result[0].url));
          });
      })
      .on('close', function() {
        winston.info(count + ' Adds requested, make sure they complete before killing task');
      });

  });
