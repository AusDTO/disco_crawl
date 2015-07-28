# This is the crawler compose file, will need to be integrated later
FROM node:latest

ENV QA_LEVEL development
ENV CRAWL_DBHOST localhost
ENV CRAWL_DBPORT 5432
ENV CRAWL_DBNAME webContent
ENV CRAWL_DBUSER webContent
ENV CRAWL_DBPASS developmentPassword
ENV CRAWL_QUEUE 1200
ENV CRAWL_MAX 0
ENV CRAWL_TIME 540
ENV CRAWL_FETCHWAIT 7
ENV CRAWL_CONC 6
ENV CRAWL_INTERVAL 200
ENV CRAWL_LOGFILE /src/logs/crawl

COPY . /src
###VOLUME /src #
VOLUME /src/logs
VOLUME /var/mail
RUN apt-get update; apt-get -y install cron vim
WORKDIR /src
RUN npm install
#Note: The following line sets up the cron job which will run wrapper.sh (and within that the crawler).
ENTRYPOINT crontab /src/config/crontab.txt; crontab -l; cron -f;
