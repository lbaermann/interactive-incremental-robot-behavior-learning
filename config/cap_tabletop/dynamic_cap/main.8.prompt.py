objects = ['yellow bowl', 'blue block', 'yellow block', 'blue bowl']
# point gripper to the corner closest to the yellow block.
closest_corner_pos = parse_position('the corner closest to the yellow block')
point_gripper_to(closest_corner_pos)
