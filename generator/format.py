def format_list(word, items):
    assert (len(items) > 0)
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return '{} {} {}'.format(items[0], word, items[1])
    else:
        return '{}, {} {}'.format(', '.join(items[:-1]), word, items[-1])
