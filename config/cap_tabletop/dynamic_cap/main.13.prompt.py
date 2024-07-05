objects = ['brown bowl', 'blue bowl', 'blue block', 'red block', 'brown block', 'red bowl']
# stack the blocks that are close to the red bowl.
close_block_names = parse_obj_name('blocks that are close to the red bowl', f'objects = {get_obj_names()}')
stack_objects_in_order(object_names=close_block_names)
