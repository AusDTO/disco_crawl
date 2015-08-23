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


describe('loadHostData Testing', function() {
  describe('Should Data Be Updated', function() {
    it('If output older than 7 days, even if newer than black/whitelist', function() {
      assert.equal(true, hostTools.shouldJobRun(moment().subtract(7, 'days').subtract(1, 'minutes'), moment().subtract(10, 'days'), moment().subtract(10, 'days')));
    });
    it('If output not older than 7 days', function() {
      assert.equal(false, hostTools.shouldJobRun(moment().subtract(7, 'days').add(1, 'minutes'), moment().subtract(10, 'days'), moment().subtract(10, 'days')));
    });
    it('If output older than whitelist', function() {
      assert.equal(true, hostTools.shouldJobRun(moment().subtract(1, 'minute'), moment().subtract(7, 'days'), moment()));
    });
    it('If output older than blacklist', function() {
      assert.equal(true, hostTools.shouldJobRun(moment().subtract(1, 'minute'), moment(), moment().subtract(7, 'days')));
    });
  });

  describe('Building Host Data', function() {
    before(function() {
      singleTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: 200
      }];
      nullHttpCodeTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: null
      }];
      emptyHttpCodeTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: ''
      }];
      redirectHttpCodeTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: 301
      }];
      errorHttpCodeTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: 505
      }];
      notFoundHttpCodeTestHost = [{
        host: 'www.testdomain.gov.au',
        minHttpCode: 404
      }];
      singleTestBlackList = [{
        host: 'www.testdomain.gov.au',
        reason: 'for a test',
        comment: 'for testing resons'
      }];
      singleTestWhitelist = [{
        host: 'www.newdomain.gov.au',
        reason: 'for a test',
        comment: 'for testing resons'
      }];
      doubleTestWhitelist = [{
        host: 'www.newdomain.gov.au',
        reason: 'for a test',
        comment: 'for testing resons'
      },{
        host: 'www.newerdomain.com.au',
        reason: 'for a test',
        comment: 'for testing resons'
      }];
      wwwDuplicateTestHosts = [{
        host: 'wwwtestdomain.gov.au',
        minHttpCode: 200
      },{
        host: 'www4.testdomain.gov.au',
        minHttpCode: 200
      },{
        host: 'www.testdomain.gov.au',
        minHttpCode: 200
      }, {
        host: 'testdomain.gov.au',
        minHttpCode: 200
      }];


    });

    describe('Setting wwwduplicate', function() {
      it('Length is not altered',
        function() {
          return hostTools.buildHostdata([], wwwDuplicateTestHosts, [], []).should.eventually.have.length(4);
        });
      it('wwwduplicate is not set on host with www in its name',
        function() {
          return hostTools.buildHostdata([], wwwDuplicateTestHosts, [], []).should.eventually.have.property(0).with.property('wwwduplicate').with.valueOf(false);
        });
      it('wwwduplicate is not set on host starting with www?.',
        function() {
          return hostTools.buildHostdata([], wwwDuplicateTestHosts, [], []).should.eventually.have.property(1).with.property('wwwduplicate').with.valueOf(false);
        });
      it('wwwduplicate is set on host starting with www. with equivilent non www version',
        function() {
          return hostTools.buildHostdata([], wwwDuplicateTestHosts, [], []).should.eventually.have.property(2).with.property('wwwduplicate').with.valueOf(true);
        });
      it('wwwduplicate is not set on equivilent non www version of host',
        function() {
          return hostTools.buildHostdata([], wwwDuplicateTestHosts, [], []).should.eventually.have.property(3).with.property('wwwduplicate').with.valueOf(false);
        });
    });

    describe('Setting serves content', function() {
      it('Length is not altered',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], []).should.eventually.have.length(1);
        });
      it('servescontent is set to true if successful',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(true);
        });
      it('servescontent is set to false if null',
        function() {
          return hostTools.buildHostdata([], nullHttpCodeTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(false);
        });
      it('servescontent is set to false if empty string',
        function() {
          return hostTools.buildHostdata([], emptyHttpCodeTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(false);
        });
      it('servescontent is set to false if redirect',
        function() {
          return hostTools.buildHostdata([], redirectHttpCodeTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(false);
        });
      it('servescontent is set to false if not found',
        function() {
          return hostTools.buildHostdata([], notFoundHttpCodeTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(false);
        });

      it('servescontent is set to false if error',
        function() {
          return hostTools.buildHostdata([], errorHttpCodeTestHost, [], []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(false);
        });

    });
    describe('Blacklisting a site', function() {
      it('Blacklisted host is retained',
        function() {
          return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, []).should.eventually.have.length(1);
        });
      it('Blacklisted flag is set',
        function() {
          return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, []).should.eventually.have.property(0).with.property('blacklisted').with.valueOf(true);
        });
      it('whitelisted flag is NOT set',
        function() {
          return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, []).should.eventually.have.property(0).with.property('whitelisted').with.valueOf(false);
        });
      it('servescontent flag is set',
        function() {
          return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, []).should.eventually.have.property(0).with.property('servescontent').with.valueOf(true);
        });

    });
    describe('Whitelisting a host', function() {
      it('Length is correct',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.length(2);
        });
      it('Original host is kept',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.property(1).with.property('host').with.valueOf(singleTestWhitelist[0].host);
        });
      it('New host is added',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.property(0).with.property('host').with.valueOf(singleTestHost[0].host);
        });

      it('Blacklisted flag is NOT set',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.property(1).with.property('blacklisted').with.valueOf(false);
        });
      it('whitelisted flag is set',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.property(1).with.property('whitelisted').with.valueOf(true);
        });
      it('servescontent flag is left null',
        function() {
          return hostTools.buildHostdata([], singleTestHost, [], singleTestWhitelist).should.eventually.have.property(1).with.property('servescontent').with.valueOf(null);
        });
        it('Two whitelisted values increases count by two',
          function() {
            return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, doubleTestWhitelist).should.eventually.have.length(9);
          });
        it('First whitelisted host is correct',
          function() {
            return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, doubleTestWhitelist).should.eventually.have.property(1).with.property('host').with.valueOf('www.newdomain.com.au');
          });
        it('Second whitelisted host is correct',
          function() {
            return hostTools.buildHostdata([], singleTestHost, singleTestBlackList, doubleTestWhitelist).should.eventually.have.property(2).with.property('host').with.valueOf('www.newerdomain.com.au');
          });

    });


  });
});
