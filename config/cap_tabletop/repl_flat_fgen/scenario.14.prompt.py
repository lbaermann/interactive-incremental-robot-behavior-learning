>>> wait_for_trigger()
{'type': 'dialog', 'text': 'stack the blocks on the top most bowl'}
>>> bowl_names = [name for name in get_obj_names() if 'bowl' in name]
>>> bowl_positions = [get_obj_pos(name) for name in bowl_names]
>>> np.argsort(bowl_positions[:, 1])[0]
2
>>> bowl_names[2]
'yellow bowl'
>>> [name for name in get_obj_names() if 'block' in name]
['green block', 'red block', 'yellow block']
>>> object_names = ['yellow bowl'] + ['green block', 'red block', 'yellow block']
>>> for i in range(len(object_names) - 1):
...     put_first_on_second(object_names[i + 1], object_names[i])


