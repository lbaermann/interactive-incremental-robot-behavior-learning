>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move objects from the green plate to the red bowl'}
>>> objects_on_green_plate = []
>>> for obj_name in get_obj_names():
...     if obj_name != 'green plate' and np.linalg.norm(get_obj_pos('green plate') - get_obj_pos(obj_name)) < 0.05:
...         objects_on_green_plate.append(obj_name)
>>> objects_on_green_plate
['green block', 'red block']
>>> for object_name in ['green block', 'red block']:
...     put_first_on_second(object_name, 'red bowl')



