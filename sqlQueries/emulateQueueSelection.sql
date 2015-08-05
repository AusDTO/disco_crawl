/* Normal Queue */
SELECT url, "nextFetchDateTime"
FROM "webDocuments"
WHERE "nextFetchDateTime" is null
ORDER BY "nextFetchDateTime" DESC
LIMIT 20;

/* Flipped Queue */
SELECT url, "nextFetchDateTime"
FROM "webDocuments"
WHERE "nextFetchDateTime" is null
ORDER BY "nextFetchDateTime"
LIMIT 20;


/*Push to never*/
UPDATE "webDocuments"
SET "nextFetchDateTime" = now() + '1000 years'
WHERE URL = '';
