import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define wiping orientation (downward-facing)
wiping_orientation = np.array([0.0, 0.0, 1.0, 0.0])  # wxyz

# Table surface is at z = 0.0; we'll wipe exactly at that height with downward orientation
wipe_z = 0.0

# Compute min and max x and y bounds based on spill center and extent
half_x = spill_extent[0] / 2
half_y = spill_extent[1] / 2

min_x = spill_position[0] - half_x
max_x = spill_position[0] + half_x
min_y = spill_position[1] - half_y
max_y = spill_position[1] + half_y

# Plan small back-and-forth wiping motions along the x-axis, stepping in y
step_size = 0.05  # Small steps to avoid large IK deltas
current_y = min_y

while current_y <= max_y:
    # Alternate direction to minimize travel distance
    if (current_y - min_y) // step_size % 2 == 0:
        x_start, x_end = min_x, max_x
    else:
        x_start, x_end = max_x, min_x
    
    # Move to start of wipe line at slightly higher z to avoid collision
    goto_pose(np.array([x_start, current_y, 0.05]), wiping_orientation)
    
    # Lower to wipe height
    goto_pose(np.array([x_start, current_y, wipe_z]), wiping_orientation)
    
    # Wipe across in current direction
    goto_pose(np.array([x_end, current_y, wipe_z]), wiping_orientation)
    
    # Step in y for next line
    current_y += step_size

# Final lift after wiping
goto_pose(np.array([spill_position[0], spill_position[1], 0.05]), wiping_orientation)