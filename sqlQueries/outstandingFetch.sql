SELECT count(*)
FROM "webDocuments"
WHERE ("nextFetchDateTime" > now()
OR "nextFetchDateTime" is null )
AND url like 'http://stat.abs.gov.au/%';
