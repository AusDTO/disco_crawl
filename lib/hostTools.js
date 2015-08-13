var fs = require('fs');
var http = require('http');
var moment = require('moment');
var Promise = require('bluebird');
var request = Promise.promisify(require('request'));
var logger = require('../config/logger');
var conf = require('../config/config');
var join = Promise.join;

module.exports = {
  shouldJobRun: function(lastOutputUpdate, lastBlacklistUpdate, lastWhitelistUpdate) {
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
  },


  buildHostdata: function(existingHosts, newHosts, blacklist, whitelist) {
    return new Promise(function(resolve, reject) {
      newHosts.forEach(function(host, index, array) {
          host.whitelisted = false;
          host.blacklisted = false;
          host.wwwduplicate = false;
          if (host.minHttpCode < 300 && host.minHttpCode !== null) {
            host.servescontent = true;
          } else {
            host.servescontent = false;
          }
          delete host.minHttpCode;
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
        }
      });

      resolve(newHosts);
    });
  }
};
