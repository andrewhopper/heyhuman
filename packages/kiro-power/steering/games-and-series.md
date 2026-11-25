# Games and multi-step flows

- Several questions: one session per question. Pass the same `run_id` so the run stream records each question and answer.
- Turn-based game: send the board with `heyhuman_start`, call `heyhuman_wait`, read the move, send the next board as a new session.
- If the agent restarts mid-flow, call `heyhuman_resume(run_id)` to pick up the open question.
