UPDATE "webDocuments"
SET "nextFetchDateTime"= ( NOW()
+ (ROUND(RANDOM()    * 2) || ' day')::INTERVAL
+ (ROUND((RANDOM()) * 24) || ' hour')::INTERVAL
+ (ROUND((RANDOM()) * 60) || ' minutes')::INTERVAL),
updated_at = now()
WHERE "nextFetchDateTime" < now() + '24 hours';
