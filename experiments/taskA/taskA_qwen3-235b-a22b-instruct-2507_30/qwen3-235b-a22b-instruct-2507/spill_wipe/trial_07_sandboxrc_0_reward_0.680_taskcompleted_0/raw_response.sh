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
stroke_step = 0.05  # 5 cm steps in y direction

# Generate back-and-forth wiping motions along x within spill bounds, stepping in y
current_y = min_y
while current_y <= max_y:
    # Left to right stroke
    left_point = np.array([min_x, current_y, wipe_z_height])
    right_point = np.array([max_x, current_y, wipe_z_height])
    
    # Move to start of stroke (left)
    goto_pose(left_point, wiping_orientation)
    
    # Perform stroke to right
    goto_pose(right_point, wiping_orientation)
    
    # Step in y for next stroke
    current_y += stroke_step
    
    # Break if we exceed bounds
    if current_y > max_y:
        break
        
    # Right to left stroke on next line
    next_left_point = np.array([min_x, current_y, wipe_z_height])
    next_right_point = np.array([max_x, current_y, wipe_z_height])
    
    # Move to start of next stroke (right side)
    goto_pose(next_right_point, wiping_orientation)
    
    # Stroke back to left
    goto_pose(next_left_point, wiping_orientation)
    
    # Step in y again
    current_y += stroke_step