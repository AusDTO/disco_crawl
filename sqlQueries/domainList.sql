SELECT host, count(*), min("httpCode") as "httpCode"
FROM "webDocuments"
GROUP BY host
HAVING min("httpCode") < 300
ORDER BY host;
