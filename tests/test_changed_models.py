import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from changed_models import PUBLISHED, models_to_build  # noqa: E402


class TestChangedModels(unittest.TestCase):
    def test_own_script_builds_only_that_model(self):
        self.assertEqual(models_to_build(["scripts/round_buddy.py"], "tweak"), ["round_buddy"])

    def test_reference_images_count_as_own_files(self):
        self.assertEqual(models_to_build(["assets/reference/gorilla/side-right.png"], ""), ["gorilla"])

    def test_shared_code_alone_builds_nothing(self):
        self.assertEqual(models_to_build(["scripts/validate_model.py", "scripts/hull.py"], "fix"), [])

    def test_tags(self):
        self.assertEqual(models_to_build([], "fix [build: gorilla, chibi_humanoid]"), ["chibi_humanoid", "gorilla"])
        self.assertEqual(models_to_build([], "[build-all]"), PUBLISHED)
        self.assertEqual(models_to_build([], "[build: nonsense]"), [])


if __name__ == "__main__":
    unittest.main()
