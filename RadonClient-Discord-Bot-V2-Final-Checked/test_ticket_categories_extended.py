import unittest
from core.ticket_categories import DEFAULT_TICKET_TYPES, effective_ticket_types

class TicketCategoryTests(unittest.TestCase):
    def test_default_count(self):
        self.assertEqual(len(DEFAULT_TICKET_TYPES), 11)
        self.assertLessEqual(len(DEFAULT_TICKET_TYPES), 15)
    def test_not_per_module(self):
        labels = [x["label"].lower() for x in DEFAULT_TICKET_TYPES]
        for module in ("auto crystal", "flight", "aim helper", "fast break"):
            self.assertFalse(any(module in label for label in labels))
    def test_removed_unavailable_categories(self):
        labels = [x["label"].lower() for x in DEFAULT_TICKET_TYPES]
        self.assertFalse(any("discord & bot" in label or "refund" in label for label in labels))
    def test_unique_ids(self):
        self.assertEqual(len({x["id"] for x in DEFAULT_TICKET_TYPES}), len(DEFAULT_TICKET_TYPES))
    def test_dropdown_lengths(self):
        for x in DEFAULT_TICKET_TYPES:
            self.assertLessEqual(len(x["id"]),100)
            self.assertLessEqual(len(x["label"]),100)
            self.assertLessEqual(len(x["description"]),100)
            self.assertTrue(x["openingPrompt"])
    def test_empty_config_fallback(self):
        self.assertEqual(len(effective_ticket_types({"tickets":{"types":[]}})), len(DEFAULT_TICKET_TYPES))
    def test_custom_preserved(self):
        custom=[{"id":"other","label":"Custom"}]
        self.assertIs(effective_ticket_types({"tickets":{"types":custom}}),custom)

if __name__ == "__main__": unittest.main()
