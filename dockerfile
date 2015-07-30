FROM node:latest
COPY . /src
###VOLUME /src #
VOLUME /src/logs
VOLUME /var/mail
WORKDIR /src
RUN apt-get update; apt-get -y install cron vim; npm install

#Copy crawler environment vars (which will be set in compose) to file so that is available in cron.
ENTRYPOINT env | grep ^CRAWL_ >> /src/crawler.env; crontab /src/config/crontab.txt; crontab -l; cron -f
