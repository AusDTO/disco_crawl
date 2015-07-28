//buildWebDocument
var crypto = require('crypto');
var conf = require('../config/config');
var logger = require('../config/logger');
//takes a queue item and builds a document with the fields I want
var moment = require('moment');

module.exports = {
  buildWebDocument: function(queueItem) {

    //DateTime is not doing timezone properly
    queueItem.lastFetchDateTime = moment().format();
    queueItem.nextFetchDateTime = moment().add(conf.get('fetchIncrement'), 'days').format();
    queueItem.httpCode = queueItem.stateData.code;
    queueItem.contentType = queueItem.stateData.contentType;
    queueItem.fetchStatus = queueItem.status;

    if (!(queueItem.document == null || queueItem.document == undefined)) {
      logger.debug('Document is not null, hashing');
      queueItem.hash = crypto.createHash('sha256').update(queueItem.document.toString()).digest('hex');
    }
    return queueItem;
  }
};
