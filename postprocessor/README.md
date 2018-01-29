# Postprocessor

This directory contains a prototype stream-based postprocessor, which uses AWS Kinesis for "fast data" style sequential processing of data sourced from the ES index that the crawler maintains.

The first script (`es2kinesis.py`) performs an ES query and pushes the result into a kinesis stream. This is not the full content (please hack it), but when we have the last step implemented (update ES with postprocessed data) then it should be changed to query something like "all records that have not been postprocessed yet" (or "up to 50K records that have not been postprocessed yet", or something like that)

The following jobs (`process_raw.py`, `process_bs4.py` and `process_goose.py`) pick-up jobs from one stream, performs some postprocessing, and push their results into the next stream. That's the basic idea.

The last job in the pipeline (doesn't exist yet) should either push updates back to ES index (I don't feel it's ready for that yet, it's still a bit raw and I don't want to blow up that index!) or write to a new, cleaned-up and enriched index. The update in-place would be simpler from "get records that haven't been postprocessed yet" perspective, or at least some combination of the two (with flags getting written back to main index, and significant new data written to a cleaned-up index).

Current steps (in order):

 * process_raw: Cleans up some unicode escape characters from the downloaded content
 * process_bs4: Creates a plain-text extract of the web content (no summarisation, just HTML stripping)
 * process_goose: Creates simple non-generative (content-based) summarisation of the page content. Basically the same as process_bs4 but without headers, footers, menus etc.


Notes:
 * the current postprocessing stages makes use of s3 for content, the only new data added to the index record on each hop is a pointer to the new content. That might not make sense for every postprocessing step.
 * TODO: checkpoint the shard iterators: the current stream behavior is to either start at TRIM_HORIZON (oldest record available) or LATEST (start at latest record). It would be much better if each postprocessor checkpointed it's stream pointer at "last sucessful", so that we could stop and resume postprocessors.
