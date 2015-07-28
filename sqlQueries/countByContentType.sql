SELECT "contentType", count(*)
  FROM "webDocuments"
  GROUP BY "contentType"
  ORDER BY "contentType";
