from data import locations

directions = {
    'west': (-1, 0),
    'east': (1, 0),
    'north': (0, -1),
    'south': (0, 1),
}

start_position = (0, 0)


def normalize_direction(raw):
    """Return the canonical direction name, or None if input is not text."""
    if not isinstance(raw, str):
        return None
    return raw.strip().lower()


def available_moves(position):
    """Return {direction: new_position} for moves that stay on the map."""
    moves = {}
    for name in sorted(directions):
        dx, dy = directions[name]
        candidate = (position[0] + dx, position[1] + dy)
        if candidate in locations:
            moves[name] = candidate
    return moves


def move(position, raw_direction):
    """Return the new position for a valid move, or None for an invalid one.

    Never raises for bad input and never mutates position, directions or
    locations, so a rejected call leaves state untouched and can be retried.
    """
    name = normalize_direction(raw_direction)
    if name is None:
        return None
    return available_moves(position).get(name)


def main(input_fn=input, output=print):
    position = start_position
    while True:
        output('you are at the %s' % locations[position])

        moves = available_moves(position)
        for name in sorted(moves):
            output('to the %s is a %s' % (name, locations[moves[name]]))

        try:
            raw = input_fn('which direction do you want to go?\n')
        except EOFError:
            output('goodbye')
            return position

        new_position = move(position, raw)
        if new_position is None:
            output("you can't go %r, try one of: %s"
                   % (raw, ', '.join(sorted(moves))))
            continue
        position = new_position


if __name__ == '__main__':
    main()
