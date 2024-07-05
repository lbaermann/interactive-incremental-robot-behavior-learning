# a diagonal line.
start_pos = denormalize_xy([0.1, 0.5])
end_pos = denormalize_xy([0.9, 0.5])
line = rotate(make_line(start=start_pos, end=end_pos), 45)
points = interpolate_pts_on_line(line=line, n=4)
ret_val = points
