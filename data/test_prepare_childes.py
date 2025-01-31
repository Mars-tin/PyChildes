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

    def test_process_basic(self):
        """Test the process_basic function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_basic('how to do it ? 36000_38606', config), 'how to do it ?')
        self.assertEqual(pc.process_basic('you need it „ right', config), 'you need it , right')
        self.assertEqual(pc.process_basic('Mommy ‡ I want some', config), 'Mommy , I want some')
        self.assertEqual(pc.process_basic('<booah:@b>', config), '<booah@b>')
        self.assertEqual(pc.process_basic('store↓', config), 'store')
        self.assertEqual(pc.process_basic('store↑', config), 'store')
        self.assertEqual(pc.process_basic('ˌbaˈna:nas', config), 'bananas')
        self.assertEqual(pc.process_basic('rhi≠noceros', config), 'rhinoceros')
        self.assertEqual(pc.process_basic('rhi^noceros', config), 'rhinoceros')
        self.assertEqual(pc.process_basic("I don't (..) know .", config), "I don't know .")
        self.assertEqual(pc.process_basic("I don't (0.15) know .", config), "I don't know .")
        self.assertEqual(pc.process_basic("I don't (1:05.15) know .", config), "I don't know .")
        self.assertEqual(pc.process_basic('(...) what do you (...) think ?', config), 'what do you think ?')
        self.assertEqual(pc.process_basic('(13.4) what do you (2.) think ?', config), 'what do you think ?')

    def test_process_local_event(self):
        """Test the process_local_event function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_local_event('&=laughs', config), '<EVT>laughs<sep><0></EVT>')
        self.assertEqual(pc.process_local_event('&=eats:cookie', config), '<EVT>eats cookie<sep><0></EVT>')
        self.assertEqual(pc.process_local_event(
            '&{l=laughs and then continue until the end marked by &}l=laughs', config),
            '<EVT>laughs and then continue until the end marked by<sep><0></EVT>'
        )
        self.assertEqual(pc.process_local_event(
            '&{n=waving:hands and then continue until the end marked by &}n=waving:hands', config),
            '<EVT>waving hands and then continue until the end marked by<sep><0></EVT>'
        )

    def test_process_linker(self):
        """Test the process_linker function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_linker(
            'smells good enough for +...', config),
            'smells good enough for ...'
        )
        self.assertEqual(pc.process_linker(
            'smells good enough for +..?', config),
            'smells good enough for ...?'
        )
        self.assertEqual(pc.process_linker(
            'smells good enough for +!?', config),
            'smells good enough for !?'
        )
        self.assertEqual(pc.process_linker(
            'what did you +/.', config),
            'what did you ...'
        )
        self.assertEqual(pc.process_linker(
            '+, with your spoon.', config),
            'with your spoon.'
        )
        self.assertEqual(pc.process_linker(
            '++ he would have come', config),
            'he would have come'
        )
        self.assertEqual(pc.process_linker(
            "+^ I really didn't", config),
            "I really didn't"
        )
        self.assertEqual(pc.process_linker(
            '+, with your spoon.', config),
            'with your spoon.'
        )
        self.assertEqual(pc.process_linker(
            'what did you +/?', config),
            'what did you ...?'
        )
        self.assertEqual(pc.process_linker(
            'smells good enough for +//.', config),
            'smells good enough for ...'
        )
        self.assertEqual(pc.process_linker(
            'smells good enough for +//?', config),
            'smells good enough for ...?'
        )
        self.assertEqual(pc.process_linker(
            'smells good enough for me +.', config),
            'smells good enough for me .'
        )
        self.assertEqual(pc.process_linker(
            'and then the little bear said +\"/.', config),
            'and then the little bear said :'
        )
        self.assertEqual(pc.process_linker(
            '+\" if you do, I\'ll carry you on my back.', config),
            "if you do, I\'ll carry you on my back."
        )
        self.assertEqual(pc.process_linker(
            'the little bear said +\".', config),
            'the little bear said .'
        )

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

    def test_process_disfluencies(self):
        """Test the process_disfluencies function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_disfluencies('&+ca dog', config), 'dog')
        self.assertEqual(pc.process_disfluencies('&-uh .', config), 'uh .')
        self.assertEqual(pc.process_disfluencies('&~wolf dog', config), '<unk> dog')

    def test_process_paralinguistic(self):
        """Test the process_paralinguistic function."""
        config = pc.ChatConfig(_TEST_CONFIG_PATH)
        self.assertEqual(pc.process_paralinguistic(
            '0 [=! laughs louder] .', config),
            '<EVT>laughs louder<sep>0</EVT> .'
        )
        self.assertEqual(pc.process_paralinguistic(
            "that's mine [=! cries] .", config),
            "that's <EVT>cries<sep>mine</EVT> ."
        )
        self.assertEqual(pc.process_paralinguistic(
            "<that's mine> [=! cries] .", config),
            "<EVT>cries<sep>that's mine</EVT> ."
        )
        self.assertEqual(pc.process_paralinguistic(
            'watch out [= laughing] .', config),
            'watch <exp>laughing<sep>out</exp> .'
        )
        self.assertEqual(pc.process_paralinguistic(
            'word [=! whispers] .', config),
            '<EVT>whispers<sep>word</EVT> .'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<first phrase> [= explains] and then <second phrase> [=! whispers]', config),
            '<exp>explains<sep>first phrase</exp> and then <EVT>whispers<sep>second phrase</EVT>'
        )
        self.assertEqual(pc.process_paralinguistic(
            'one [=! laughs] and two [= comments]', config),
            '<EVT>laughs<sep>one</EVT> and <exp>comments<sep>two</exp>'
        )
        self.assertEqual(pc.process_paralinguistic(
            'Billy, would you please <take your shoes off> [!]', config),
            'Billy, would you please <stress>take your shoes off</stress>'
        )
        self.assertEqual(pc.process_paralinguistic(
            'Billy, would you please <take your shoes off> [!!]', config),
            'Billy, would you please <stress>take your shoes off</stress>'
        )
        self.assertEqual(pc.process_paralinguistic(
            'where does that [!] go ?', config),
            'where does <stress>that</stress> go ?'
        )
        self.assertEqual(pc.process_paralinguistic(
            'where does that [!!] go ?', config),
            'where does <stress>that</stress> go ?'
        )
        self.assertEqual(pc.process_paralinguistic(
            'Use word [# 3.1] when needed', config),
            'Use word when needed'
        )
        self.assertEqual(pc.process_paralinguistic(
            'I could use <all of them> [# 2.2] for the party', config),
            'I could use all of them for the party'
        )
        self.assertEqual(pc.process_paralinguistic(
            'I could use <all of them> [# 2.2] [=! whispers] for the party', config),
            'I could use <EVT>whispers<sep>all of them</EVT>'
        )
        self.assertEqual(pc.process_paralinguistic(
            "whyncha [: why don't you] just be quiet !", config),
            "why don't you just be quiet !"
        )
        self.assertEqual(pc.process_paralinguistic(
            'goed [: went]', config),
            'went'
        )
        self.assertEqual(pc.process_paralinguistic(
            'goed [: went] [*]', config),
            'went'
        )
        self.assertEqual(pc.process_paralinguistic(
            'we want <one or two> [=? one too]', config),
            'we want one or two'
        )
        self.assertEqual(pc.process_paralinguistic(
            "I really wish you wouldn't [% said with strong raising of eyebrows] do that", config),
            "I really wish you <exp>said with strong raising of eyebrows<sep>wouldn't</exp> do that"
        )
        self.assertEqual(pc.process_paralinguistic(
            '<going away with my mommy> [?] ?', config),
            'going away with my mommy ?'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<&~diddliddleiddle> [>]', config),
            '&~diddliddleiddle'
        )
        self.assertEqual(pc.process_paralinguistic(
            'no (.) Sarah (.) you have to <stop doing that> [>] !', config),
            'no (.) Sarah (.) you have to stop doing that !'
        )
        self.assertEqual(pc.process_paralinguistic(
            "<Mommy I don't like this> [<]", config),
            "Mommy I don't like this"
        )
        self.assertEqual(pc.process_paralinguistic(
            'and the <doggy was> [>1] really cute and it <had to go> [>2] into bed', config),
            'and the doggy was really cute and it had to go into bed'
        )
        self.assertEqual(pc.process_paralinguistic(
            '+< they had to go in here', config),
            'they had to go in here'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<I wanted> [/] I wanted to invite Margie', config),
            'I wanted to invite Margie'
        )
        self.assertEqual(pc.process_paralinguistic(
            "it's [/] (.) &-um (.) it's [/] it's (.) a &-um (.) dog", config),
            "(.) &-um (.) it's (.) a &-um (.) dog"
        )
        self.assertEqual(pc.process_paralinguistic(
            "<it's it's it's> [/] it's (.) a &-um (.) dog", config),
            "it's (.) a &-um (.) dog"
        )
        self.assertEqual(pc.process_paralinguistic(
            "it's [x 3] it's (.) a &-um (.) dog", config),
            "it's (.) a &-um (.) dog"
        )
        self.assertEqual(pc.process_paralinguistic(
            '<I wanted> [//] &-uh I thought I wanted to invite Margie', config),
            'I wanted ... &-uh I thought I wanted to invite Margie'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<the fish is> [//] the [/] the fish are swimming', config),
            'the fish is ... the fish are swimming'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<all of my friends had> [///] uh we all decided to go home for lunch', config),
            'all of my friends had ... uh we all decided to go home for lunch'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<I wanted> [/-] uh when is Margie coming', config),
            'I wanted ... uh when is Margie coming'
        )
        self.assertEqual(pc.process_paralinguistic(
            '<I think that maybe> [e] the cat is up the tree', config),
            'the cat is up the tree'
        )
        self.assertEqual(pc.process_paralinguistic(
            'I think that maybe the cat is up the tree [+ exc]', config),
            ''
        )
        self.assertEqual(pc.process_paralinguistic(
            'The pig has not yet fed [^c err]', config),
            'The pig has not yet fed'
        )
        self.assertEqual(pc.process_paralinguistic(
            " I'll get it. [+ bch]", config),
            ''
        )
        self.assertEqual(pc.process_paralinguistic(
            '0. [+ trn]', config),
            '0.'
        )
        self.assertEqual(pc.process_paralinguistic(
            'not this one. [+ neg] [- req] [+ inc]', config),
            'not this one.'
        )
