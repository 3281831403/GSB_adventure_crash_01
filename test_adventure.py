import copy
import unittest

import adventure
from adventure import (
    describe,
    exits,
    move,
    normalize_direction,
    play,
    directions,
    INVALID_MESSAGE,
    START_POSITION,
)
from data import locations

HOUSE = (0, 0)
LAKE = (0, 1)
PARK = (1, 0)
MARKET = (1, 1)

# Every legal move on the fixed map.
LEGAL_MOVES = [
    (HOUSE, 'east', PARK),
    (HOUSE, 'south', LAKE),
    (LAKE, 'north', HOUSE),
    (LAKE, 'east', MARKET),
    (PARK, 'west', HOUSE),
    (PARK, 'south', MARKET),
    (MARKET, 'west', LAKE),
    (MARKET, 'north', PARK),
]

# Case / whitespace tolerance must not change the result.
class NormalizeDirectionTests(unittest.TestCase):

    def test_01_all_directions_canonical(self):
        for name in directions:
            self.assertEqual(normalize_direction(name), name)

    def test_02_case_insensitive_and_trimmed(self):
        cases = [
            ('EAST', 'east'), ('West', 'west'),
            ('  north  ', 'north'), ('\tSOUTH\n', 'south'),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_direction(raw), expected)

    def test_03_illegal_arguments_return_none(self):
        for bad in [None, '', '   ', 'up', 'eastwest', '1', '\n\t',
                    3, 1.5, ['east'], ('north',), {'south': 1}, object()]:
            with self.subTest(bad=bad):
                self.assertIsNone(normalize_direction(bad))


class ExitsTests(unittest.TestCase):

    def test_04_exit_table_matches_map(self):
        expected = {
            HOUSE: [('east', PARK), ('south', LAKE)],
            LAKE: [('east', MARKET), ('north', HOUSE)],
            PARK: [('west', HOUSE), ('south', MARKET)],
            MARKET: [('west', LAKE), ('north', PARK)],
        }
        for position, want in expected.items():
            with self.subTest(position=position):
                self.assertEqual(exits(position), want)

    def test_05_exits_order_is_canonical_and_deterministic(self):
        first = exits(HOUSE)
        for _ in range(20):
            self.assertEqual(exits(HOUSE), first)
        names = [name for name, _ in first]
        self.assertEqual(names, sorted(names,
                                       key=adventure.CANONICAL_DIRECTIONS.index))

    def test_06_every_location_covered_single_and_boundary(self):
        reachable = set()
        for position in locations:
            reachable.update(destination for _, destination in exits(position))
            self.assertTrue(exits(position))  # no dead-ends on this map
        self.assertEqual(reachable, set(locations))


class MoveTests(unittest.TestCase):

    def test_07_legal_moves_table_driven(self):
        for position, raw, destination in LEGAL_MOVES:
            with self.subTest(position=position, raw=raw):
                new_position, message = move(position, raw)
                self.assertEqual(new_position, destination)
                self.assertIsNone(message)

    def test_08_legal_moves_accept_case_and_whitespace(self):
        for position, raw, destination in [
            (HOUSE, ' EAST ', PARK),
            (PARK, '\tsouth\n', MARKET),
            (LAKE, 'NORTH', HOUSE),
            (MARKET, '  West  ', LAKE),
        ]:
            with self.subTest(position=position, raw=raw):
                self.assertEqual(move(position, raw), (destination, None))

    def test_09_blocked_directions_are_illegal(self):
        blocked = [
            (HOUSE, 'north'), (HOUSE, 'west'),
            (LAKE, 'south'), (LAKE, 'west'),
            (PARK, 'north'), (PARK, 'east'),
            (MARKET, 'east'), (MARKET, 'south'),
        ]
        for position, name in blocked:
            with self.subTest(position=position, name=name):
                self.assertEqual(move(position, name),
                                 (position, INVALID_MESSAGE))

    def test_10_unknown_and_non_string_input(self):
        for bad in ['up', '', '   ', 'n', 'east east', None, 7, [], {}]:
            with self.subTest(bad=bad):
                self.assertEqual(move(HOUSE, bad),
                                 (HOUSE, INVALID_MESSAGE))

    def test_11_failure_is_rollback_then_success_succeeds(self):
        position = HOUSE
        snapshot = copy.deepcopy(position)
        for bad in ['north', 'west', '  UP ', '', None]:
            position, message = move(position, bad)
            self.assertEqual(position, snapshot)
            self.assertEqual(message, INVALID_MESSAGE)
        position, message = move(position, 'east')
        self.assertEqual(position, PARK)
        self.assertIsNone(message)

    def test_12_repeated_calls_are_stable(self):
        position = HOUSE
        for _ in range(50):
            position, message = move(position, 'east')
            self.assertEqual(position, PARK)
            self.assertIsNone(message)
            position, message = move(position, 'west')
            self.assertEqual(position, HOUSE)
            self.assertIsNone(message)

    def test_13_failed_repeated_calls_never_move(self):
        position = MARKET
        for _ in range(30):
            position, message = move(position, 'east')
            self.assertEqual(position, MARKET)
        position, message = move(position, 'north')
        self.assertEqual((position, message), (PARK, None))

    def test_14_multi_turn_walk_and_back(self):
        script = ['south', 'east', 'north', 'west']  # house-lake-market-park
        position = HOUSE
        path = []
        for raw in script:
            position, message = move(position, raw)
            self.assertIsNone(message)
            path.append(position)
        self.assertEqual(path, [LAKE, MARKET, PARK, HOUSE])
        self.assertEqual(position, START_POSITION)

    def test_15_mixed_valid_invalid_multi_turn(self):
        steps = [('up', HOUSE), ('east', PARK), ('north', PARK),
                 ('south', MARKET), ('  WEST  ', LAKE),
                 ('west', LAKE), ('north', HOUSE)]
        position = HOUSE
        for raw, expected in steps:
            position, message = move(position, raw)
            self.assertEqual(position, expected)
        self.assertEqual(position, HOUSE)


class DescribeTests(unittest.TestCase):

    def test_16_describe_is_stable_and_deterministic(self):
        first = describe(HOUSE)
        for _ in range(20):
            self.assertEqual(describe(HOUSE), first)
        self.assertEqual(first, [
            'you are at the house',
            'to the east is a park',
            'to the south is a lake',
        ])

    def test_17_describe_single_exit_style_at_every_location(self):
        for position in locations:
            lines = describe(position)
            self.assertEqual(len(lines), 1 + len(exits(position)))
            self.assertTrue(lines[0].startswith('you are at the '))


class PlayTests(unittest.TestCase):

    class ScriptedReader(object):
        def __init__(self, answers):
            self.answers = list(answers)
            self.calls = 0

        def __call__(self, prompt):
            self.calls += 1
            if not self.answers:
                raise EOFError
            return self.answers.pop(0)

    def _run(self, answers, start=HOUSE):
        output = []
        reader = self.ScriptedReader(answers)
        final = play(copy.deepcopy(start), reader, output.append)
        return final, output, reader

    def test_18_invalid_direction_does_not_crash_and_continues(self):
        final, output, reader = self._run(['up', ' EAST ', 'west'])
        self.assertEqual(final, HOUSE)
        self.assertIn(INVALID_MESSAGE, output)
        # One prompt per answer, then one more prompt that signals EOF.
        self.assertEqual(reader.calls, 4)
        joined = '\n'.join(output)
        self.assertIn('you are at the park', joined)
        self.assertIn('you are at the house', joined)

    def test_19_replay_same_input_is_deterministic(self):
        script = ['north', 'east', 'bad', ' south ', 'west',
                  '  ', 'EAST', 'north']
        run1 = self._run(script)[1]
        run2 = self._run(copy.deepcopy(script))[1]
        self.assertEqual(run1, run2)
        # Direct replay of the pure move API must also match exactly.
        def replay():
            position = HOUSE
            trace = []
            for raw in script:
                position, message = move(position, raw)
                trace.append((position, message))
            return trace
        self.assertEqual(replay(), replay())

    def test_20_eof_on_empty_input_returns_start_unchanged(self):
        final, output, reader = self._run([])
        self.assertEqual(final, HOUSE)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(output, describe(HOUSE))

    def test_21_no_state_growth_across_many_turns(self):
        state_keys = ('directions', 'CANONICAL_DIRECTIONS',
                      'INVALID_MESSAGE', 'START_POSITION', 'locations')
        before = copy.deepcopy({k: getattr(adventure, k) for k in state_keys})
        position = HOUSE
        for _ in range(500):
            for raw in ('east', 'nope', 'west', '  '):
                position, _ = move(position, raw)
        self.assertEqual(position, HOUSE)
        after = {k: getattr(adventure, k) for k in state_keys}
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
