objects = ['orange bowl', 'red block',  'purple block', 'orange block', 'purple bowl', 'red bowl']
# point gripper to any three points in a horizontal line in the middle
n_points = 3
place_positions = parse_position(f'a horizontal line in the middle with {n_points} points')
for line_position in place_positions:
    point_gripper_to(line_position)
