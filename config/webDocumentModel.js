    var Sequelize = require('sequelize');

    module.exports = function(sequelize, DataTypes) {
      return sequelize.define('webDocument', {
        url: {
          name: 'url',
          type: Sequelize.TEXT,
          allowNull: false,
          primaryKey: true,
          isUrl: true
        },
        host: {
          name: 'host',
          type: Sequelize.STRING
        },
        document: {
          name: 'document',
          type: Sequelize.BLOB
        },

        lastFetchDateTime: {
          name: 'last_fetch_date_time',
          type: Sequelize.DATE
        },
        nextFetchDateTime: {
          name: 'next_fetch_date_time',
          type: Sequelize.DATE
        },
        path: {
          name: 'path',
          type: Sequelize.TEXT
        },
        port: {
          name: 'port',
          type: Sequelize.INTEGER
        },
        protocol: {
          name: 'protocol',
          type: Sequelize.STRING
        },
        httpCode: {
          name: 'http_code',
          type: Sequelize.INTEGER
        },
        contentType: {
          name: 'content_type',
          type: Sequelize.STRING
        },
        stateData: {
          name: 'state_data',
          type: Sequelize.JSON
        },
        fetchStatus: {
          name: 'fetch_status',
          type: Sequelize.STRING
        },
        fetched: {
          name: 'fetched',
          type: Sequelize.BOOLEAN
        },
        //NOTE: This is not yet populated
        outlinks: {
          name: 'outlinks',
          type: Sequelize.ARRAY(Sequelize.TEXT)
        },
        hash: {
          name: 'hash',
          type: Sequelize.STRING
        },
        version: {
          name: 'version',
          type: Sequelize.INTEGER
        }
      }, {
        underscored: true,
        indexes: [
          // Create a unique index on email
          {
            name: 'url',
            unique: true,
            method: 'BTREE',
            fields: ['url']
          }, {
            name: 'lastFetchDateTime',
            method: 'BTREE',
            fields: ['lastFetchDateTime']
          }, {
            name: 'nextFetchDateTime',
            method: 'BTREE',
            fields: ['nextFetchDateTime']
          }, {
            name: 'host',
            method: 'BTREE',
            fields: ['host']
          }, {
            name: 'httpCode',
            method: 'BTREE',
            fields: ['httpCode']
          }, {
            name: 'fetchStatus',
            method: 'BTREE',
            fields: ['fetchStatus']
          }
        ]
      });
    };
