var logger = require('winston');
var conf = require('./config.js');
var stdLog = conf.get('logFile') + '_std.log';
var errLog = conf.get('logFile') + '_err.log';


if (conf.get('debug')) {

    logger.remove(winston.transports.Console);

  logger.add(winston.transports.Console, {
    level: 'debug'
  });

  logger.add(winston.transports.File, {
    name: 'standard',
    filename: stdLog,
    level: 'debug',
    maxsize: (25 * 1024 * 1024 ) //bytes
  });
  logger.add(winston.transports.File, {
    name: 'error',
    filename: errLog,
    level: 'error'
  });
  logger.info('Debug logging enabled');
} else {
  logger.transports.Console.level = 'info';
  //logger.remove(winston.transports.Console);
  logger.add(winston.transports.File, {
    name: 'standard',
    filename: stdLog,
    level: 'info'
  });
  logger.add(winston.transports.File, {
    name: 'error',
    filename: errLog,
    level: 'error'
  });
}

logger.info('Logging Configured');
logger.debug('Debug Messages Included');
module.exports = logger;
