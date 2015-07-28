UPDATE "webDocuments"
SET "nextFetchDateTime"= ( NOW() + (14 + (ROUND(RANDOM()) * 3) || ' day')::INTERVAL
+ (ROUND((RANDOM()) * 24) || ' hour')::INTERVAL), updated_at = now()
WHERE url like '' 
AND "nextFetchDateTime" is null;
