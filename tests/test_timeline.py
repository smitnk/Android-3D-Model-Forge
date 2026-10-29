import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "animation"))
import timeline  # noqa: E402


class TimelineTest(unittest.TestCase):
    def test_shots_cover_all_frames_without_gaps(self):
        shots = timeline.shot_frames(24, 8)
        self.assertEqual(shots[0][0], 1)
        self.assertEqual(shots[-1][1], 192)
        for a, b in zip(shots, shots[1:]):
            self.assertEqual(a[1] + 1, b[0])
        self.assertEqual(len({s[2] for s in shots}), 3)  # three distinct camera positions

    def test_captions_deterministic_and_ordered(self):
        a = timeline.caption_words("one two | three", 6)
        self.assertEqual(a, timeline.caption_words("one two | three", 6))
        self.assertEqual(a, [("one", 0.0, 2.0), ("two", 2.0, 4.0), ("three", 4.0, 6.0)])
        self.assertEqual(timeline.caption_words("  ", 8), [])

    def test_filter_strips_unsafe_chars(self):
        f = timeline.drawtext_filter("it's 100%: ok", 8, "/f.ttf", 1280)
        self.assertIn("text='ITS'", f)
        self.assertIn("text='100'", f)
        self.assertEqual(f.count("drawtext="), 3)


if __name__ == "__main__":
    unittest.main()
