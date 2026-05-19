# Arvexo Study Content Sources

## Current State

`data/task.json` is currently built from the FIPI open bank and partially enriched with NeoFamily matches.

Current local coverage:

- total tasks: 1293
- tasks with `correct_answer`: 71
- tasks without `correct_answer`: 1222

## Source Assessment

### FIPI Open Bank

Use for task discovery and format reference only until usage rights are clarified.

Pros:

- official source for task formats;
- stable enough for mapping exam numbers and topics.

Cons:

- the open bank pages do not expose answers for most tasks;
- commercial reuse rights need legal confirmation.

### Official FIPI Demo / Open Variant PDFs

Best low-risk source for a small seed set.

Pros:

- official documents include answer tables;
- answer formats are authoritative;
- good for demo/trial content and validation tests.

Cons:

- small volume;
- tasks are variant-based, not a full bank.

Recommended use:

- import only the public demo/open variants with explicit attribution;
- keep source URL and document year in `source`;
- do not treat this as enough for the full MVP bank.

### NeoFamily

Technically useful for matching answers, already supported by `tools/neofamily_answers_to_task_json.py`.

Risk:

- it is a third-party educational platform;
- mass copying answers/solutions into a commercial product should not be shipped without permission or a license.

Recommended use:

- keep only as an internal research/prototyping aid;
- do not publish copied answer data until rights are cleared.

### СДАМ ГИА / Решу ЕГЭ

Technically has many tasks with answers and solutions.

Risk:

- license terms describe the site/content as licensed software/content for user access;
- scraping or reproducing their task/answer database in a competing product is high risk without permission.

Recommended use:

- do not scrape for production;
- contact for permission/licensing if this source is important.

### 100points / Other Commercial Prep Sites

Some pages advertise banks with answers.

Risk:

- likely proprietary course/content material;
- unsuitable for bulk copying without a direct agreement.

Recommended use:

- do not scrape for production;
- only use with written permission or partner agreement.

### fipi-ege.ru and Similar Aggregators

Some aggregators claim to provide FIPI answers.

Risk:

- unclear provenance and licensing;
- data quality may be inconsistent;
- using them can compound the same FIPI rights problem.

Recommended use:

- use only for manual cross-checking during editorial review;
- do not auto-import into production without source validation.

## Recommended MVP Pipeline

1. Keep FIPI tasks in `draft` until an answer is verified.
2. Create an editorial queue for tasks without answers.
3. Fill answers from one of:
   - official demo/open variant answer tables;
   - teacher/manual solving;
   - licensed partner content;
   - AI-assisted solving followed by human validation.
4. Store provenance per answer:
   - `answer_source`;
   - `answer_verified_by`;
   - `answer_verified_at`;
   - `confidence`;
   - `rights_status`.
5. Publish only tasks with `rights_status = "cleared"` and verified answers.

## Practical MVP Recommendation

For the first 100 tasks:

1. Use existing FIPI parser to collect candidate tasks.
2. Do not try to fill all 1293 answers automatically.
3. Pick 100 tasks across numbers 1-18.
4. Solve/verify them manually or through a teacher.
5. Use NeoFamily/other sites only as a comparison signal, not as the final source of truth.

This is slower than scraping, but it avoids building the product on content that may need to be removed later.
