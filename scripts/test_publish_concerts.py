import unittest

from publish_concerts import identity, merge


class PublishTests(unittest.TestCase):
    def test_merge_same_event(self):
        a = {"date": "2027-01-01", "time": "14:00", "venue": "NHKホール",
             "title": "定期演奏会", "workIds": ["a"], "composerIds": ["x"]}
        b = dict(a, workIds=["b"], composerIds=["y"])
        self.assertEqual(len(merge([a, b])), 1)
        self.assertEqual(merge([a, b])[0]["workIds"], ["a", "b"])

    def test_distinct_start_times(self):
        a = {"date": "2027-01-01", "time": "14:00", "venue": "NHKホール", "title": "定期演奏会"}
        self.assertNotEqual(identity(a), identity(dict(a, time="19:00")))
