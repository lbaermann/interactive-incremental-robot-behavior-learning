>>> wait_for_trigger()
{'type': 'dialog', 'text': 'place the blue block in the empty bowl'}
>>> bowl_names = [name for name in get_obj_names() if 'bowl' in name]
>>> get_empty_bowls()
['yellow bowl']
>>> put_first_on_second('blue block', 'yellow bowl')
'success'
