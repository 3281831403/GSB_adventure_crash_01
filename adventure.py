from data import locations

try:
    input = raw_input
except NameError:
    pass


# Direction name -> coordinate delta.
directions = {
    'west': (-1, 0),
    'east': (1, 0),
    'north': (0, -1),
    'south': (0, 1),
}

# Fixed order so advertised exits never depend on hash or dict iteration order.
CANONICAL_DIRECTIONS = ('west', 'east', 'north', 'south')

INVALID_MESSAGE = "you can't go that way"

START_POSITION = (0, 0)


def normalize_direction(text):
    """Return the canonical direction name for user input.

    Leading/trailing whitespace and letter case are ignored. Unknown or
    non-text input returns None instead of raising.
    """
    try:
        name = text.strip().lower()
    except AttributeError:
        return None
    if name in directions:
        return name
    return None


def exits(position):
    """Return a deterministic list of (direction, destination) for exits."""
    result = []
    for name in CANONICAL_DIRECTIONS:
        delta_x, delta_y = directions[name]
        possible_position = (position[0] + delta_x, position[1] + delta_y)
        if possible_position in locations:
            result.append((name, possible_position))
    return result


def move(position, direction_text):
    """Attempt one move.

    Returns (new_position, message). On an invalid direction the position is
    returned unchanged together with a readable message: the attempted move
    is fully rolled back and no state is mutated.
    """
    name = normalize_direction(direction_text)
    destinations = dict(exits(position))
    if name is None or name not in destinations:
        return position, INVALID_MESSAGE
    return destinations[name], None


def describe(position):
    """Return the lines shown to the player for one turn."""
    lines = ['you are at the %s' % locations[position]]
    for name, possible_position in exits(position):
        lines.append('to the %s is a %s'
                     % (name, locations[possible_position]))
    return lines


def play(position=START_POSITION, reader=input, writer=print):
    """Run the game loop; invalid directions report and continue."""
    while True:
        for line in describe(position):
            writer(line)
        try:
            direction_text = reader('which direction do you want to go?\n')
        except EOFError:
            return position
        position, message = move(position, direction_text)
        if message is not None:
            writer(message)


def main():
    play()


if __name__ == '__main__':
    main()
