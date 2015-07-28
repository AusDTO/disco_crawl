SELECT count(*), "fetchStatus"
  FROM "webDocuments"
  GROUP BY "fetchStatus"
  ORDER BY "fetchStatus";
