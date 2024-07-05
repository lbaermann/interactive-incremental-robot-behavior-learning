>>> wait_for_trigger()
{'type': 'dialog', 'text': 'point gripper to any three points in a horizontal line in the middle'}
>>> start_pos = denormalize_xy([0.1, 0.5])
>>> end_pos = denormalize_xy([0.9, 0.5])
>>> points = interpolate_pts_on_line(start=start_pos, end=end_pos, n=3)
>>> for point in points:
...     point_gripper_to(point)
