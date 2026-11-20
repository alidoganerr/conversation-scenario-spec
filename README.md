# conversation-scenario-spec

A JSON format for describing a practice conversation, and a validator for it.

I wanted a plain file that a role-play script, a chatbot test or a training exercise could all read, without tying it to any one tool. So it stays small on purpose: who is talking, where, what they're trying to get done, and which moments are worth looking at afterwards.

## Fields

- `id`, `title`, `version` (like `1.0.0`), `language` (`en`, `tr-TR`, ...)
- `setting`: `situation`, `channel` (`voice`, `text` or `video`), and an optional `max_turns`
- `participant`: the role the person plays, plus a short brief
- `counterpart`: the simulated person (`name`, `role`, `background`, `starting_mood`)
- `objective`
- `opening_message`, the counterpart's first line
- `key_moments`, a list of `{"id", "description"}`

The full JSON Schema is in `scenario.schema.json`. There are two examples, `example_study_room.json` and `example_it_support_triage.json`. The people in them are made up.

## Running it

```
python3 validate.py example_*.json
```

It prints every problem it finds and exits with 1 if any file is invalid, so it works as a CI step. Standard library only, Python 3.9+.

The validator is a little stricter than the schema: it also rejects strings that are only whitespace.

Tests: `python3 -m unittest`

Ali Doğaner. MIT licensed.
