#Overview
This application crawls all gov.au domains (excluding states and territories) and stores the resouces
found in a database. It is the intent that other components of the discovery layer will then modify and
enhance that crawled information to support an improved user experience.

It is a node application largely based on the simplecrawler project integrated with postgres.


##Options
There are a large set of options available to control the crawler behavior. These can be altered through environment variables or as command line parameters. Refer to the config/config.js file for information.
