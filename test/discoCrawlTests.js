var moment = require('moment');
var crypto = require('crypto');

var conf = require('../config/config');
var crawlRules = require("../lib/crawlRules");
var logger = require('../config/logger');
var util = require('../lib/buildWebDocument');
var hostTools = require('../lib/hostTools');

var chai = require("chai");
var assert = chai.assert;
var should = require('chai').should();
var chaiAsPromised = require("chai-as-promised");
chai.use(chaiAsPromised);

describe('discoCrawl Testing', function() {
  describe('Ensure tests are working', function() {
    it('Array function test', function() {
      assert.equal(-1, [1, 2, 3].indexOf(5));
      assert.equal(-1, [1, 2, 3].indexOf(0));
    });
  });


  //modules loading

  //config defaults
  describe('configDefaults', function() {
    it('debug is false', function() {
      assert.equal(conf.get('debug'), false);
    });
    it('initQueueSize is 100', function() {
      assert.equal(conf.get('initQueueSize'), 100);
    });
    it('maxItems is 0', function() {
      assert.equal(conf.get('maxItems'), 0);
    });
    it('timeToRun is 240', function() {
      assert.equal(conf.get('timeToRun'), 240);
    });
    it('fetchIncrement is 7', function() {
      assert.equal(conf.get('fetchIncrement'), 7);
    });
    it('concurrency is 4', function() {
      assert.equal(conf.get('concurrency'), 4);
    });
    it('interval (between fetches) is 2000', function() {
      assert.equal(conf.get('interval'), 2000);
    });
    it('logFile is ./logs/crawl', function() {
      assert.equal(conf.get('logFile'), './logs/crawl');
    });
    it('dbHost is localhost', function() {
      assert.equal(conf.get('dbHost'), 'localhost');
    });
    it('dbPort is 5432', function() {
      assert.equal(conf.get('dbPort'), 5432);
    });

    it('dbUser is webConent', function() {
      assert.equal(conf.get('dbUser'), 'webContent');
    });

    it('dbPass is developmentPassword', function() {
      assert.equal(conf.get('dbPass'), 'developmentPassword');
    });

    it('dbName is webContent', function() {
      assert.equal(conf.get('dbName'), 'webContent');
    });
    it('flipOrder is false', function() {
      assert.equal(conf.get('flipOrder'), false);
    });
  });


  //domain regex
  describe('crawlRules', function() {
    describe('#commDomain()', function() {
      it('should return false when a state domain', function() {
        assert.equal(crawlRules.commDomain({
          host: 'sa.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'vic.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'www.vic.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'something.qld.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'something.wa.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'www.something.wa.gov.au'
        }), false);
        assert.equal(crawlRules.commDomain({
          host: 'nt.gov.au'
        }), false);
      });

      it('should return true when commonwealth domain', function() {
        assert.equal(crawlRules.commDomain({
          host: 'humanservices.gov.au'
        }), true);
        assert.equal(crawlRules.commDomain({
          host: 'ramint.gov.au'
        }), true);
        assert.equal(crawlRules.commDomain({
          host: 'nfsa.gov.au'
        }), true);
        assert.equal(crawlRules.commDomain({
          host: 'dto.gov.au'
        }), true);
        assert.equal(crawlRules.commDomain({
          host: 'www.humanservices.gov.au'
        }), true);
        assert.equal(crawlRules.commDomain({
          host: 'trove.nla.gov.au'
        }), true);
      });
    });


    it('should return false when non-gov domain', function() {
      assert.equal(crawlRules.commDomain({
        host: 'twitter.com'
      }), false);
      assert.equal(crawlRules.commDomain({
        host: 'google.com.au'
      }), false);
    });


    //non gov.au


    describe('#notExcludedDomain()', function() {
      it('should return false for excluded domain', function() {
        assert.equal(crawlRules.notExcludedDomain({
          host: 'pandora.nla.gov.au'
        }), false);
        assert.equal(crawlRules.notExcludedDomain({
          host: 'trove.nla.gov.au'
        }), false);
      });

      it('should return true for non-excluded domain', function() {
        assert.equal(crawlRules.notExcludedDomain({
          host: 'humanservices.gov.au'
        }), true);
        assert.equal(crawlRules.notExcludedDomain({
          host: 'environment.gov.au'
        }), true);
      });
    });


    //url regex

    describe('#notExcludedUrl()', function() {
      it('should return false for australian cancer trial search', function() {
        assert.equal(crawlRules.notExcludedUrl({
          host: 'www.australiancancertrials.gov.au',
          path: '/search-clinical-trials/search-results.aspx?kw=&t=&s=&p=&ph=&int=&df=&dt=&ps=&fs=&min=&max=&units=&gen=&loc=&et=&rs=',
          protocol: 'http'
        }), false);
      });
      it('should return false for browsing law.ato', function() {
        assert.equal(crawlRules.notExcludedUrl({
          host: 'law.ato.gov.au',
          path: '/atolaw/Browse.htm?ImA=folder&Node=5~3~1~4~0&OpenNodes=5~3~1,5~3~1~4,5,5~3&DBTOC=06%3AATO%20Rulings%20and%20Determinations%20%28Including%20GST%20Bulletins%29%3ACompendium%3ARulings%3ASuperannuation%20Guarantee%3A2009#5~3~1~4~0',
          protocol: 'http'
        }), false);
      });
      it('should return true for viewing australian cancer trials)', function() {
        assert.equal(crawlRules.notExcludedUrl({
          host: 'www.australiancancertrials.gov.au',
          path: '/search-clinical-trials/search-results/clinical-trials-details.aspx?TrialID=368447&ds=1',
          protocol: 'http'
        }), true);
      });
      it('should return true for viewing law.ato)', function() {
        assert.equal(crawlRules.notExcludedUrl({
          host: 'http://law.ato.gov.au',
          path: '/atolaw/view.htm?dbwidetocone=06%3AATO%20Rulings%20and%20Determinations%20%28Including%20GST%20Bulletins%29%3ACompendium%3ARulings%3ASuperannuation%20Guarantee%3A2009%3A%2304910010000%23SGR%202009%2F1EC%20-%20Compendium%3B',
          protocol: 'http'
        }), true);
      });
    });

    //maxItems: function(parsedURL, crawler)
  });

  //Need to get a sample document
  var mockQueueItem = {
    url: "http://fake.host.gov.au/some/random/path/and/file2.html",
    host: "fake.host.gov.au",
    path: "/",
    port: 80,
    protocol: "https",
    document: "Some HTML Text",
    stateData: {
      requestLatency: 437,
      requestTime: 819,
      contentLength: 40427,
      contentType: "text/html; charset=utf-8",
      code: 200,
      headers: {
        date: "Mon, 22 Jun 2015 11:46:42 GMT",
        server: "Apache",
        p3p: "CP=\"NOI ADM DEV PSAi COM NAV OUR OTRo STP IND DEM\"",
        cachecontrol: "no-cache, max-age=600",
        pragma: "no-cache",
        setcookie: [
          "3d9b206e19a45952c4f378835b6dd7da=6203c0407623d08051063ed18f7920f7; path=/"
        ],
        expires: "max-age=29030400, public",
        vary: "Accept-Encoding",
        contentlength: "40427",
        connection: "close",
        contenttype: "text/html; charset=utf-8"
      },
      downloadTime: 382,
      actualDataSize: 40427,
      sentIncorrectSize: false
    },
    status: "Downloaded",
    fetched: true
  };

  var mockDocument = {};

  describe('buildWebDocument', function() {
    describe('#buildWebDocument()', function() {
      before(function() {
        mockDocument = util.buildWebDocument(mockQueueItem);
      });
      it('should set the httpCode', function() {
        assert.propertyVal(mockDocument, 'httpCode', 200);
      });
      it('should set the status', function() {
        assert.propertyVal(mockDocument, 'fetchStatus', 'Downloaded');
      });
      it('should set the contentType', function() {
        assert.propertyVal(mockDocument, 'contentType', 'text/html; charset=utf-8');
      });
      it('should set a hash', function() {
        assert.propertyVal(mockDocument, 'hash', crypto.createHash('sha256').update(mockDocument.document.toString()).digest('hex'));
      });
      it('should set the next fetch for ' + conf.get('fetchIncrement') + 'days', function() {
        assert.isBelow(moment(mockDocument.nextFetchDateTime).valueOf(), moment().add(7, 'days').valueOf());
        assert.closeTo(moment(mockDocument.nextFetchDateTime).valueOf(), moment().add(7, 'days').valueOf(), 1000);
      });
      it('should set a last fetch after and near the current time', function() {
        assert.isBelow(moment(mockDocument.lastFetchDateTime).valueOf(), moment().valueOf());
        assert.closeTo(moment(mockDocument.lastFetchDateTime).valueOf(), moment().valueOf(), 1000);
      });
    });
  });
});
