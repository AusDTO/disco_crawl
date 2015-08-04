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
WHERE URL = '"https://www.comlaw.gov.au/Details/C2011C00765/9ede0f0c-1f47-418e-978b-0e7fb8976c3c_files/image007.gif"';
