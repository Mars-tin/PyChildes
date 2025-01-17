"""Tests for the functions in prepare_childes.py."""
import os
import unittest

import prepare_childes as pc

_TEST_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'configs/example.yaml')


class TestPrepareChildes(unittest.TestCase):
    """Tests for the functions in prepare_childes.py."""

    def test_process_header(self):
        """Test the process_header function."""
        header = '@Content'
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_header(header, config), (False, '@Content'))

    def test_process_unidentifiable(self):
        """Test the process_unidentifiable function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_unidentifiable('xxx', config), '<unk>')
        self.assertEqual(pc.process_unidentifiable('yyy', config), '<unk>')
        self.assertEqual(pc.process_unidentifiable('www', config), '<unk>')

        self.assertEqual(pc.process_unidentifiable('xxx yyy ww', config), '<unk> <unk> ww')

        self.assertEqual(pc.process_unidentifiable('<CHI> xxx yyy', config), '<CHI> <unk> <unk>')

    def test_process_special_form(self):
        """Test the process_special_form function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)

        # Babbling (@b)
        # synthetic utterances
        self.assertEqual(pc.process_special_form('x@b', config), '<unk>')
        self.assertEqual(pc.process_special_form('xxx@b yyy', config), '<unk> yyy')
        self.assertEqual(pc.process_special_form('word x@b', config), 'word <unk>')
        # real utterances
        self.assertEqual(
            pc.process_special_form('da_ba_da_ba_doo@b .', config),
            '<unk> .'
        )
        self.assertEqual(pc.process_special_form('ba@b .', config), '<unk> .')

        # Child-invented forms (@c)
        # synthetic utterances
        self.assertEqual(pc.process_special_form('x@c', config), '<unk>')
        self.assertEqual(pc.process_special_form('xxx@c yyy', config), '<unk> yyy')
        self.assertEqual(pc.process_special_form('word x@c', config), 'word <unk>')
        # real utterances
        self.assertEqual(
            pc.process_special_form('wakey_up@c (55.) .', config),
            '<unk> (55.) .'
        )
        self.assertEqual(
            pc.process_special_form('a dubby^dubby^do@c (4.) .', config),
            'a <unk> (4.) .'
        )

        # Dialect forms (@d) with words kept
        config.utterance['specform']['dialect'] = True
        # synthetic utterances
        self.assertEqual(pc.process_special_form('x@d', config), 'x')
        self.assertEqual(pc.process_special_form('xxx@d yyy', config), 'xxx yyy')
        self.assertEqual(pc.process_special_form('word x@d', config), 'word x')

        # Dialect forms (@d) with words replaced
        config.utterance['specform']['dialect'] = False
        # synthetic utterances
        self.assertEqual(pc.process_special_form('x@d', config), '<unk>')
        self.assertEqual(pc.process_special_form('xxx@d yyy', config), '<unk> yyy')
        self.assertEqual(pc.process_special_form('word x@d', config), 'word <unk>')
