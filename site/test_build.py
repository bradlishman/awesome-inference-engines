import unittest

from build import load_catalogue


class CatalogueTests(unittest.TestCase):
    def test_catalogue_is_generated_from_canonical_markdown(self):
        result = load_catalogue()
        self.assertGreaterEqual(result["counts"]["all"], 60)
        self.assertGreaterEqual(result["counts"]["documented"], 15)
        self.assertEqual(result["counts"]["all"], len(result["projects"]))

    def test_compatibility_is_grounded(self):
        projects = {entry["name"]: entry for entry in load_catalogue()["projects"]}
        self.assertEqual(projects["Basalt"]["compatibility"]["status"], "upstream-documented")
        self.assertIn("Blackwell", projects["Basalt"]["compatibility"]["target"])
        self.assertTrue(projects["Basalt"]["compatibility"]["evidence"])
        self.assertIsNone(projects["llama.cpp"]["compatibility"])


if __name__ == "__main__":
    unittest.main()
