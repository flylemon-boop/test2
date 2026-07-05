import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define wiping orientation (downward-facing)
wiping_orientation = np.array([0, 0, 1, 0])  # wxyz

# Compute bounds for wiping motion based on spill center and extent
half_length_x = spill_extent[0] / 2
half_length_y = spill_extent[1] / 2

min_x = spill_position[0] - half_length_x
max_x = spill_position[0] + half_length_x
min_y = spill_position[1] - half_length_y
max_y = spill_position[1] + half_length_y

# Number of passes in y-direction
num_passes = 5
y_step = (max_y - min_y) / num_passes

# Small overlap between motions to ensure full coverage
overlap = 0.02

# Perform back-and-forth wiping motions along x, stepping in y
for i in range(num_passes + 1):
    y_current = min_y + i * y_step
    
    # Alternate direction for each pass to reduce large motions
    if i % 2 == 0:
        start_x, end_x = max_x, min_x
    else:
        start_x, end_x = min_x, max_x
    
    # First move to the starting point above the surface
    goto_pose(np.array([start_x, y_current, 0.0]), wiping_orientation)
    
    # Wipe horizontally at table height (z=0.0)
    goto_pose(np.array([end_x, y_current, 0.0]), wiping_orientation)

# Final stabilization pose
goto_pose(spill_position, wiping_orientation)