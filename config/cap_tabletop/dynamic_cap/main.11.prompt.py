objects = ['brown bowl', 'green block', 'brown block', 'green bowl', 'blue bowl', 'blue block']
# place the green block in the bowl closest to the middle.
middle_bowl_name = parse_obj_name('the bowl closest to the middle', f'objects = {get_obj_names()}')
put_first_on_second('green block', middle_bowl_name)
