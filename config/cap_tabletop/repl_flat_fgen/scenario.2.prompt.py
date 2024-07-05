>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the pinkish colored block on the bottom side'}
>>> get_obj_names()
['pink block', 'gray block', 'orange block']
>>> bottom_side_pos = denormalize_xy([0.5, 0])
>>> put_first_on_second('pink block', bottom_side_pos)
'success'