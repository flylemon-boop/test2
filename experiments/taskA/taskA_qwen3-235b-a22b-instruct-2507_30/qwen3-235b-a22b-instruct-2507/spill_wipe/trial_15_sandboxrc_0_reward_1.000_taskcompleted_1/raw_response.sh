import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define the wiping orientation (downward-facing)
wiping_orientation = np.array([0, 0, 1, 0])  # wxyz

# Compute bounds for wiping based on spill position and extent
half_extent_x = spill_extent[0] / 2
half_extent_y = spill_extent[1] / 2

min_x = spill_position[0] - half_extent_x
max_x = spill_position[0] + half_extent_x
min_y = spill_position[1] - half_extent_y
max_y = spill_position[1] + half_extent_y

# Define small overlap between strokes to ensure full coverage
step_size = 0.05  # 5 cm steps for smooth and safe motions

# Generate a back-and-forth wiping pattern along the x-axis, stepping in y
current_y = min_y
reversed_direction = False  # alternate direction per row

while current_y <= max_y:
    # Determine start and end x based on current pass direction
    if reversed_direction:
        x_start, x_end = max_x, min_x
    else:
        x_start, x_end = min_x, max_x

    # Move to start point at table height (z=0.0)
    goto_pose(np.array([x_start, current_y, 0.0]), wiping_orientation)

    # Wipe to end point
    goto_pose(np.array([x_end, current_y, 0.0]), wiping_orientation)

    # Step in y for next pass
    current_y += step_size
    reversed_direction = not reversed_direction  # Alternate direction