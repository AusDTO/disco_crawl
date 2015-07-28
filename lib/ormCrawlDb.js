var Sequelize = require('sequelize');
var moment = require('moment');
var Promise = require('bluebird');
var conf = require('../config/config.js');
var logger = require('../config/logger');

//TODO: Add flag for query logging

module.exports = {
    db: new Sequelize(
        conf.get('dbName'),
        conf.get('dbUser'),
        conf.get('dbPass'), {
            host: conf.get('dbHost'),
            dialect: 'postgres',
            pool: {
                max: 6,
                min: 0,
                idle: 10000
            }, logging: null
        }),

    webDocument: null,

    get: function() {
        return this;
    },
//TODO: Look at adding a randomise function as per...
//           SELECT myid FROM mytable OFFSET floor(random()*N) LIMIT 1;
    connect: function() {
        orm = this;
        return new Promise(function(resolve, reject) {
            orm.db.authenticate()
                .then(function() {
                    logger.debug("Authenticated");
                    orm.db.import('../config/webDocumentModel');
                    //WARN: Uncommenting this will delete the database and recreate it.
                    //orm.db.sync({force: true})
                    orm.db.sync()
                    .then(function() {
                        logger.info("Synced");
                        resolve(orm);
                    })
                    .catch(function(e) {
                        logger.error("Sync Failed:" + e);
                    });
                    orm.webDocument = orm.db.model('webDocument');
                    resolve(orm);
                })
                .catch(function(e) {
                    logger.error("Connection Failed");
                    reject(e);
                });
        });
    },

    newQueueList: function(limit) {
        orm = this;

        var configOrder;
        if (conf.get('flipOrder')) {
          configOrder = [['nextFetchDateTime'], ['created_at', 'DESC']];
        } else {
          configOrder = [['nextFetchDateTime', 'DESC'], ['created_at']];
        }

        return new Promise(function(resolve, reject) {
            var now = moment().format();
            orm.webDocument.findAll({
                where: Sequelize.or({
                    nextFetchDateTime: {
                        lte: now
                    }
                    }, {
                        nextFetchDateTime: null
                    }),
                order: configOrder,
                limit:limit
            })
            .then(function(result) {
                resolve(result);
            })
                .catch(function(e) {
                    logger.error("Queue Select Failed: " + e);
                    reject(e);
                });
        });
    },



    upsert: function(document) {
        logger.debug("Upserting: " + document.url);
        orm = this;

        //logger.debug(webDocument);
        return new Promise(function(resolve, reject) {
            webDocument = orm.db.model('webDocument');
            webDocInstance =webDocument.upsert(document)
                .then(function(result, created) {
                    logger.debug('Upsert Result: ' + result);
                    resolve(result);
                })
                .catch(function(e) {
                    logger.error("upsert rejecting" + e);
                    logger.error("Document: " + JSON.stringify(document));
                    logger.error("webDocument.url: " + JSON.stringify(webDocument.url));
                    logger.error("webDocument: " + JSON.stringify(webDocument));
                    process.exit()
                    reject(e);
                });

            //TODO Validate the document first

        });
    },

    readyForFetch: function(url) {
        orm = this;
        return new Promise(function(resolve, reject) {
            orm.webDocument.findOne({
                where: {
                    url: url
                }
            })
            //TODO CHECK NULL TREATMENT
            .then(function(result) {
                if (result !== null) {
                    if (result.nextFetchDateTime <= moment()) {
                        logger.debug("Url: " + url + " is ready to fetch");
                        resolve(true);
                    } else {
                        logger.debug("Url: " + url + " is not ready to fetch");
                        resolve(false);
                    }
                } else {
                    logger.debug("Url: " + url + " is ready to fetch (not found)");
                    resolve(true);
                }
            })
                .catch(function(e) {
                    logger.error("Date Check Failed for: " + JSON.stringify(url) + "error: " + e);
                    process.exit();
                });
        });
    },



    addIfMissing: function(document) {
        orm = this;
        return new Promise(function(resolve, reject) {
            orm.webDocument.findOrCreate({
                where: {
                    url: document.url
                },
                host: document.host
            })
                .then(function(result, newRow) {
                    if (newRow) {
                        logger.debug('addIfMissing Added URL: ' + document.url);
                    } else {
                        logger.debug('addIfMisssing URL Existed: ' + document.url);
                    }
                    resolve(result, newRow);
                })
                .catch(function(e) {
                    logger.error('addIfMissing Failed for url: ' + document.url);
                    logger.error('addIfMissing Result Error: ' + e);
                    reject(e);
                });
        });
    }


};
