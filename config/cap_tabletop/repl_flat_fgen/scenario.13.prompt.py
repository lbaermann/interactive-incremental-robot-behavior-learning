>>> wait_for_trigger()
{'type': 'dialog', 'text': 'stack the blocks that are close to the red bowl'}
>>> close_object_names = get_objects_close_to(point=get_obj_pos('red bowl'))
>>> [name for name in close_object_names if 'block' in name]
['green block', 'pink block', 'red block']
>>> put_first_on_second('pink block', 'green block')
'success'
>>> put_first_on_second('red block', 'pink block')
'success'