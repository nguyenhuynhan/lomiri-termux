#!/usr/bin/env python3
"""Regression checks for focus races, manual dismissal and orientation."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from keyboard_policy import KeyboardPolicy


class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.policy = KeyboardPolicy((672, 1339))

    def show(self):
        self.assertTrue(self.policy.request(True))
        self.policy.viewport((672, 705))
        self.assertTrue(self.policy.owned)

    def test_manual_dismissal_is_not_undone_by_viewport_events(self):
        self.show()
        self.policy.viewport((672, 1339))
        self.assertFalse(self.policy.owned)
        self.assertIsNone(self.policy.request(True))
        self.assertIsNone(self.policy.request(False))
        self.assertTrue(self.policy.request(True))

    def test_automatically_opened_keyboard_closes_after_focus_loss(self):
        self.show()
        self.assertFalse(self.policy.request(False))
        self.policy.viewport((672, 1339))
        self.assertFalse(self.policy.owned)

    def test_manually_opened_keyboard_is_not_closed(self):
        self.policy.viewport((672, 705))
        self.assertIsNone(self.policy.request(True))
        self.assertIsNone(self.policy.request(False))

    def test_focus_lost_while_android_is_opening_is_reconciled(self):
        self.assertTrue(self.policy.request(True))
        self.assertIsNone(self.policy.request(False))
        self.policy.viewport((672, 705))
        self.assertFalse(self.policy.reconcile())

    def test_rotation_has_its_own_full_height(self):
        self.policy.viewport((1339, 672))
        self.assertFalse(self.policy.visible)
        self.assertTrue(self.policy.request(True))
        self.policy.viewport((1339, 400))
        self.assertTrue(self.policy.visible)

    def test_disabling_auto_does_not_open_the_keyboard(self):
        self.assertIsNone(self.policy.request(True, False))
        self.assertTrue(self.policy.request(True, True))

    def test_rotation_with_keyboard_open_preserves_visibility_and_ownership(self):
        self.show()
        self.policy.viewport((1339, 400))
        self.assertTrue(self.policy.visible)
        self.assertTrue(self.policy.owned)
        self.assertIsNone(self.policy.request(True))
        self.assertFalse(self.policy.request(False))

    def test_tapping_a_focused_input_reopens_a_manually_dismissed_keyboard(self):
        self.show()
        self.policy.viewport((672, 1339))
        self.assertTrue(self.policy.request(True, force=True))


if __name__ == '__main__':
    unittest.main()
