# Postprocessor
1;4804;0c
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
 * TODO: Checkpoint the shard iterators: The current stream behavior is to either start at TRIM_HORIZON (oldest record available) or LATEST (start at latest record). It would be much better if each postprocessor checkpointed it's stream pointer at "last sucessful", so that we could stop and resume postprocessors. This would remove the need for TRIM_HORIZON settings (behavior would start at the beginning unless checkpoint exists, else start at checkpoint). 
 * TODO: tune number of shards so that job can complete in a reasonable time
 * TODO: use checkpoint infrastructure (shared state) to lock shard iterators; such that we can have multiple nodes in parallel and each shard ends up getting processed by exactly one node. Or not, this might be a little funky especially if dynamic - instead maybe just scale-up the node so it can handle a processes for every shard.
 * TODO: add processor for "DNS cleanup". Currently, we have some corrupt domain names (caused by mangled mailto: links in pages that we aren't handling gracefully). We could add a cleanup task to chomp `foo@` from them -> cleaned_domain attribute.
 * TODO: add processor for readability score (using goose/NLTK summary).
 * TODO: output processor that flags post-processing state in primary index.
 * TODO: refactor processors (bs4, goose) so they append data to field rather than s3 (performance hack - only write to s3 if DEBUG or something like that. It was useful for development but not interesting except at the end)
 * TODO: use firehose to write content to s3 (outside of the pipeline)
 * TODO: create "experimental LTSM generative summariser" processor
 * TODO: create TF-IDF keyword processor
 * TODO: create KMeans clustering processor
 * TODO: create deep learning keyword extractor
 * TODO: create deep learning cluster processor
 * TODO: create keyword/cluster-based recommendation array
