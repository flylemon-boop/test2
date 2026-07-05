# Code block 0
import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define wiping orientation (downward-facing)
wiping_orientation = np.array([0, 0, 1, 0])  # wxyz

# Table surface height is z = 0.0 m
wipe_z_height = 0.0

# Calculate bounds for wiping based on spill position and extent
half_length_x = spill_extent[0] / 2
half_length_y = spill_extent[1] / 2

min_x = spill_position[0] - half_length_x
max_x = spill_position[0] + half_length_x
min_y = spill_position[1] - half_length_y
max_y = spill_position[1] + half_length_y

# Small overlap between strokes to ensure full coverage
stroke_step = 0.05  # 5 cm step for overlapping strokes

# Generate back-and-forth wiping pattern along y-axis, moving incrementally in x
current_y = min_y
while current_y <= max_y:
    # Wipe from min_x to max_x at current_y
    goto_pose(np.array([min_x, current_y, wipe_z_height]), wiping_orientation)
    goto_pose(np.array([max_x, current_y, wipe_z_height]), wiping_orientation)
    
    # Move to next parallel line if still within bounds
    current_y += stroke_step
    if current_y > max_y:
        break
        
    # Return stroke from max_x to min_x at updated y
    goto_pose(np.array([max_x, current_y, wipe_z_height]), wiping_orientation)
    goto_pose(np.array([min_x, current_y, wipe_z_height]), wiping_orientation)
    
    # Increment y again for next pass
    current_y += stroke_step