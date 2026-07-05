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
y_direction = 1  # Start moving in positive y direction

# Move to starting point above the spill area
start_position = np.array([min_x, min_y, wipe_z_height])
goto_pose(start_position, wiping_orientation)

# Perform grid-like wiping motion within the spill bounds
x = min_x
while x <= max_x:
    # Determine stroke endpoints in y for current x
    y_start = min_y
    y_end = max_y
    
    # Move to start of stroke at current x
    stroke_start = np.array([x, y_start, wipe_z_height])
    goto_pose(stroke_start, wiping_orientation)
    
    # Wipe to end of stroke
    stroke_end = np.array([x, y_end, wipe_z_height])
    goto_pose(stroke_end, wiping_orientation)
    
    # Increment x for next parallel stroke
    x += stroke_step