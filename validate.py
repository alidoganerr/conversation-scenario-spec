#!/usr/bin/env python3
"""Check conversation scenario files.

Usage:
    python validate.py scenario.json [more.json ...]

Exit code is 0 when every file is valid, 1 otherwise.
"""
import json
import re
import sys

ID = re.compile(r"[a-z0-9][a-z0-9-]*", re.ASCII)
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)
LANGUAGE = re.compile(r"[a-z]{2}(-[A-Z]{2})?", re.ASCII)
CHANNELS = ("voice", "text", "video")

TOP = {"id", "title", "version", "language", "setting", "participant",
       "counterpart", "objective", "opening_message", "key_moments"}


def _matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _text(value, minimum=1):
    return isinstance(value, str) and len(value.strip()) >= minimum


def _section(data, name, required, allowed, errors):
    # A missing section has already been reported as a missing top-level key.
    if name not in data:
        return None
    section = data[name]
    if not isinstance(section, dict):
        errors.append(f"{name}: must be an object")
        return None
    for key in sorted(required - section.keys()):
        errors.append(f"{name}: missing '{key}'")
    for key in sorted(section.keys() - allowed):
        errors.append(f"{name}: unknown field '{key}'")
    return section


def _check_text(obj, key, minimum, where, errors):
    if key in obj and not _text(obj[key], minimum):
        suffix = "" if minimum == 1 else f" ({minimum} characters or more)"
        errors.append(f"{where}.{key}: must be text{suffix}")


def validate(data):
    """Return a list of problems, empty if the scenario is valid."""
    if not isinstance(data, dict):
        return ["scenario: must be an object"]
    errors = []
    for key in sorted(TOP - data.keys()):
        errors.append(f"scenario: missing '{key}'")
    for key in sorted(data.keys() - TOP):
        errors.append(f"scenario: unknown field '{key}'")

    if "id" in data and not _matches(ID, data["id"]):
        errors.append("id: use lowercase letters, digits and dashes")
    if "title" in data and not _text(data["title"], 3):
        errors.append("title: must be text (3 characters or more)")
    if "version" in data and not _matches(VERSION, data["version"]):
        errors.append("version: use MAJOR.MINOR.PATCH, for example 1.0.0")
    if "language" in data and not _matches(LANGUAGE, data["language"]):
        errors.append("language: use a code such as 'en' or 'tr-TR'")
    if "objective" in data and not _text(data["objective"], 10):
        errors.append("objective: must be text (10 characters or more)")
    if "opening_message" in data and not _text(data["opening_message"]):
        errors.append("opening_message: must be text")

    setting = _section(data, "setting", {"situation", "channel"},
                       {"situation", "channel", "max_turns"}, errors)
    if setting is not None:
        _check_text(setting, "situation", 10, "setting", errors)
        if "channel" in setting and not (isinstance(setting["channel"], str)
                                         and setting["channel"] in CHANNELS):
            errors.append("setting.channel: one of " + ", ".join(CHANNELS))
        turns = setting.get("max_turns")
        if "max_turns" in setting and not (isinstance(turns, int)
                                           and not isinstance(turns, bool) and turns >= 2):
            errors.append("setting.max_turns: whole number, at least 2")

    participant = _section(data, "participant", {"role", "brief"}, {"role", "brief"}, errors)
    if participant is not None:
        _check_text(participant, "role", 1, "participant", errors)
        _check_text(participant, "brief", 10, "participant", errors)

    required = {"name", "role", "background", "starting_mood"}
    counterpart = _section(data, "counterpart", required, required, errors)
    if counterpart is not None:
        _check_text(counterpart, "name", 1, "counterpart", errors)
        _check_text(counterpart, "role", 1, "counterpart", errors)
        _check_text(counterpart, "background", 10, "counterpart", errors)
        _check_text(counterpart, "starting_mood", 1, "counterpart", errors)

    moments = data.get("key_moments")
    if "key_moments" in data:
        if not isinstance(moments, list) or not moments:
            errors.append("key_moments: a list with at least one entry")
        else:
            seen = set()
            for i, moment in enumerate(moments):
                where = f"key_moments[{i}]"
                if not isinstance(moment, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                for key in sorted({"id", "description"} - moment.keys()):
                    errors.append(f"{where}: missing '{key}'")
                for key in sorted(moment.keys() - {"id", "description"}):
                    errors.append(f"{where}: unknown field '{key}'")
                mid = moment.get("id")
                if "id" in moment:
                    if not _matches(ID, mid):
                        errors.append(f"{where}.id: use lowercase letters, digits and dashes")
                    elif mid in seen:
                        errors.append(f"{where}.id: '{mid}' is used twice")
                    else:
                        seen.add(mid)
                _check_text(moment, "description", 10, where, errors)
    return errors


def main(paths):
    if not paths:
        print(__doc__)
        return 1
    failed = False
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError, RecursionError) as exc:
            # JSONDecodeError and UnicodeDecodeError are both ValueErrors
            print(f"{path}: cannot read ({type(exc).__name__})")
            failed = True
            continue
        errors = validate(data)
        if errors:
            failed = True
            print(f"{path}: {len(errors)} problem(s)")
            for message in errors:
                print(f"  - {message}")
        else:
            print(f"{path}: ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
