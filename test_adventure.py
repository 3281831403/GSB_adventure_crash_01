import copy
import unittest

import adventure
from data import locations


def run_game(inputs):
    """Drive adventure.main with scripted inputs; return (outputs, final_pos)."""
    outputs = []
    remaining = list(inputs)

    def fake_input(prompt=''):
        outputs.append(prompt.rstrip('\n'))
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    final_position = adventure.main(input_fn=fake_input, output=outputs.append)
    return outputs, final_position


class NormalizeDirectionTests(unittest.TestCase):
    def test_table_driven_normalization(self):
        cases = [
            ('east', 'east'),
            ('EAST', 'east'),
            ('East', 'east'),
            ('  east', 'east'),
            ('east  ', 'east'),
            ('\tNoRtH\n', 'north'),
            ('', ''),
            ('   ', ''),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(expected, adventure.normalize_direction(raw))

    def test_non_string_returns_none(self):
        for bad in (None, 123, 4.5, ['east'], ('east',), object()):
            with self.subTest(bad=bad):
                self.assertIsNone(adventure.normalize_direction(bad))


class MoveTests(unittest.TestCase):
    def test_legal_moves_from_every_position(self):
        cases = [
            ((0, 0), 'east', (1, 0)),
            ((0, 0), 'south', (0, 1)),
            ((1, 0), 'west', (0, 0)),
            ((1, 0), 'south', (1, 1)),
            ((0, 1), 'north', (0, 0)),
            ((0, 1), 'east', (1, 1)),
            ((1, 1), 'north', (1, 0)),
            ((1, 1), 'west', (0, 1)),
        ]
        for position, direction, expected in cases:
            with self.subTest(position=position, direction=direction):
                self.assertEqual(expected, adventure.move(position, direction))

    def test_invalid_moves_return_none(self):
        cases = [
            ((0, 0), 'west'),    # off the map
            ((0, 0), 'north'),   # off the map
            ((1, 1), 'east'),    # off the map
            ((1, 1), 'south'),   # off the map
            ((0, 0), 'up'),      # unknown direction word
            ((0, 0), ''),        # empty input
            ((0, 0), '   '),     # whitespace only
            ((0, 0), 'easts'),   # near miss
        ]
        for position, direction in cases:
            with self.subTest(position=position, direction=direction):
                self.assertIsNone(adventure.move(position, direction))

    def test_case_and_whitespace_tolerated(self):
        for raw in ('EAST', 'East', ' east ', '\teAsT\n'):
            with self.subTest(raw=raw):
                self.assertEqual((1, 0), adventure.move((0, 0), raw))

    def test_non_string_input_returns_none(self):
        for bad in (None, 42, ['east']):
            with self.subTest(bad=bad):
                self.assertIsNone(adventure.move((0, 0), bad))

    def test_rejected_call_leaves_state_identical(self):
        snapshot_directions = copy.deepcopy(adventure.directions)
        snapshot_locations = copy.deepcopy(locations)
        position = (0, 0)
        self.assertIsNone(adventure.move(position, 'nowhere'))
        self.assertEqual((0, 0), position)
        self.assertEqual(snapshot_directions, adventure.directions)
        self.assertEqual(snapshot_locations, locations)

    def test_success_after_failure_unaffected(self):
        position = (0, 0)
        self.assertIsNone(adventure.move(position, 'bogus'))
        self.assertEqual((1, 0), adventure.move(position, 'east'))

    def test_repeated_calls_round_trip(self):
        position = (0, 0)
        for _ in range(3):
            position = adventure.move(position, 'east')
            self.assertEqual((1, 0), position)
            position = adventure.move(position, 'west')
            self.assertEqual((0, 0), position)

    def test_module_state_does_not_grow_after_many_calls(self):
        before = (len(adventure.directions), len(locations))
        for _ in range(1000):
            adventure.move((0, 0), 'east')
            adventure.move((0, 0), 'bogus')
        self.assertEqual(before, (len(adventure.directions), len(locations)))


class AvailableMovesTests(unittest.TestCase):
    def test_moves_per_position(self):
        cases = [
            ((0, 0), {'east': (1, 0), 'south': (0, 1)}),
            ((1, 0), {'west': (0, 0), 'south': (1, 1)}),
            ((0, 1), {'north': (0, 0), 'east': (1, 1)}),
            ((1, 1), {'north': (1, 0), 'west': (0, 1)}),
        ]
        for position, expected in cases:
            with self.subTest(position=position):
                self.assertEqual(expected, adventure.available_moves(position))


class MainLoopTests(unittest.TestCase):
    def test_invalid_direction_prints_hint_and_continues(self):
        outputs, final = run_game(['teleport', 'east'])
        self.assertTrue(any("you can't go" in line for line in outputs))
        self.assertEqual((1, 0), final)

    def test_messy_input_is_accepted(self):
        outputs, final = run_game(['  SoUtH\t', ' EAST '])
        self.assertEqual((1, 1), final)
        self.assertFalse(any("you can't go" in line for line in outputs))

    def test_multi_turn_walk_around_the_map(self):
        _, final = run_game(['east', 'south', 'west', 'north'])
        self.assertEqual((0, 0), final)

    def test_eof_exits_cleanly(self):
        outputs, final = run_game([])
        self.assertEqual((0, 0), final)
        self.assertIn('goodbye', outputs[-1])

    def test_same_input_sequence_is_deterministic(self):
        inputs = ['east', 'bogus', 'south', ' WEST ', 'north']
        first = run_game(inputs)
        second = run_game(list(inputs))
        self.assertEqual(first, second)

    def test_failure_then_success_within_session(self):
        outputs, final = run_game(['west', 'west', 'east'])
        self.assertEqual(2, sum("you can't go" in line for line in outputs))
        self.assertEqual((1, 0), final)


if __name__ == '__main__':
    unittest.main()
