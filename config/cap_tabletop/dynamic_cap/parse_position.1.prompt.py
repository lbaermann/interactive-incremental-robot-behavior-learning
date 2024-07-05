# a horizontal line in the middle with 3 points.
start_pos = denormalize_xy([0.1, 0.5])
end_pos = denormalize_xy([0.9, 0.5])
line = make_line(start=start_pos, end=end_pos)
points = interpolate_pts_on_line(line=line, n=3)
ret_val = points