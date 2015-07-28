SELECT host, count(*)
FROM "webDocuments"
WHERE "nextFetchDateTime" < now() + '24 hours'
GROUP BY host
ORDER BY host;



/* A 24 Hour Period      */


SELECT host, count(*)
FROM "webDocuments"
WHERE "nextFetchDateTime" > now() + '1 days'
AND   "nextFetchDateTime" < now() + '3 days'
GROUP BY host
ORDER BY host;




/*Push Back */


UPDATE "webDocuments"
SET "nextFetchDateTime"= "nextFetchDateTime" + '7 days'
updated_at = now()
WHERE "nextFetchDateTime" < now() + '24 hours';
