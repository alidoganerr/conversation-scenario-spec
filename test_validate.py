import copy
import glob
import json
import unittest

from validate import validate


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class Examples(unittest.TestCase):
    def test_examples(self):
        paths = glob.glob("example_*.json")
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(validate(load(path)), [])


class Rejections(unittest.TestCase):
    def setUp(self):
        self.base = load("example_study_room.json")

    def broken(self, edit):
        data = copy.deepcopy(self.base)
        edit(data)
        return validate(data)

    def test_missing_field(self):
        errors = self.broken(lambda d: d.pop("objective"))
        self.assertIn("scenario: missing 'objective'", errors)

    def test_unknown_field(self):
        errors = self.broken(lambda d: d.update(foo=1))
        self.assertIn("scenario: unknown field 'foo'", errors)

    def test_bad_version(self):
        for value in ("1.0", "1.0.0\n", "١.٠.٠"):
            with self.subTest(value=value):
                errors = self.broken(lambda d: d.update(version=value))
                self.assertTrue(any(e.startswith("version") for e in errors))

    def test_id_newline(self):
        errors = self.broken(lambda d: d.update(id="ok\n"))
        self.assertTrue(any(e.startswith("id") for e in errors))

    def test_channel(self):
        for value in ("carrier-pigeon", ["voice"], {"a": 1}, None):
            with self.subTest(value=value):
                errors = self.broken(lambda d: d["setting"].update(channel=value))
                self.assertTrue(any(e.startswith("setting.channel") for e in errors))

    def test_section_not_object(self):
        for name in ("setting", "participant", "counterpart"):
            with self.subTest(name=name):
                errors = self.broken(lambda d: d.update({name: None}))
                self.assertIn(f"{name}: must be an object", errors)

    def test_non_text_fields(self):
        errors = self.broken(lambda d: d["counterpart"].update(name=5, starting_mood=["x"]))
        self.assertTrue(any(e.startswith("counterpart.name") for e in errors))
        self.assertTrue(any(e.startswith("counterpart.starting_mood") for e in errors))

    def test_max_turns(self):
        for value in (1, True, 2.5, "9"):
            with self.subTest(value=value):
                errors = self.broken(lambda d: d["setting"].update(max_turns=value))
                self.assertTrue(any(e.startswith("setting.max_turns") for e in errors))

    def test_duplicate_key_moment(self):
        def edit(d):
            d["key_moments"][1]["id"] = d["key_moments"][0]["id"]
        self.assertTrue(any("used twice" in e for e in self.broken(edit)))

    def test_empty_key_moments(self):
        errors = self.broken(lambda d: d.update(key_moments=[]))
        self.assertTrue(any(e.startswith("key_moments") for e in errors))

    def test_not_an_object(self):
        self.assertEqual(validate([]), ["scenario: must be an object"])


if __name__ == "__main__":
    unittest.main()
