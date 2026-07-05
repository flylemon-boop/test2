# Code block 0
import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define wiping parameters based on spill extent
half_length_x = spill_extent[0] / 2
half_length_y = spill_extent[1] / 2

# Set the wiping bounds
min_x = spill_position[0] - half_length_x
max_x = spill_position[0] + half_length_x
min_y = spill_position[1] - half_length_y
max_y = spill_position[1] + half_length_y

# Use downward-facing orientation for wiping (z-axis down)
wiping_orientation = np.array([0, 0, 1, 0])  # wxyz

# Wipe in a grid pattern with small overlapping motions to avoid large IK jumps
num_strips = 5
y_positions = np.linspace(min_y, max_y, num_strips)

for i, y in enumerate(y_positions):
    # Alternate direction for each pass to reduce motion discontinuities
    x_range = np.linspace(max_x, min_x, 10) if i % 2 == 1 else np.linspace(min_x, max_x, 10)
    for x in x_range:
        goto_pose(np.array([x, y, 0.0]), wiping_orientation)