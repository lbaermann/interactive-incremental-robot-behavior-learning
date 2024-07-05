objects = ['orange bowl', 'red block',  'purple block', 'orange block', 'purple bowl', 'red bowl']
# point gripper to k points in a diagonal line, where k is the number of bowls
bowl_names = parse_obj_name('the bowls', f'objects = {get_obj_names()}')
k = len(bowl_names)
place_positions = parse_position(f'a diagonal line with {k} points')
for line_position in place_positions:
    point_gripper_to(line_position)
