objects = ['brown bowl', 'green block', 'brown block', 'green bowl', 'blue bowl', 'blue block']
# move the left most block to the green bowl.
left_block_name = parse_obj_name('left most block', f'objects = {get_obj_names()}')
put_first_on_second(left_block_name, 'green bowl')
