>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the pinkish colored block on the bottom side'}
>>> get_obj_names()
['pink block', 'gray block', 'orange block']
>>> bottom_side_pos = parse_position('the bottom side')
>>> put_first_on_second('pink block', bottom_side_pos)
'failure'
>>> bottom_side_pos = parse_position('bottom')
>>> put_first_on_second('pink block', bottom_side_pos)
'failure'
>>> bottom_side_pos = parse_position('bottom side')
>>> put_first_on_second('pink block', bottom_side_pos)
'failure'
>>> # This looks like a loop. Abort
... wait_for_trigger()