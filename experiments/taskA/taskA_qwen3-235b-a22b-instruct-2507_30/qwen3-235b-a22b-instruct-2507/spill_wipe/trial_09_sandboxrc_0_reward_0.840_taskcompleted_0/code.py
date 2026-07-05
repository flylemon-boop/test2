# Code block 0
import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define wiping parameters based on spill extent
half_length_x = spill_extent[0] / 2
half_length_y = spill_extent[1] / 2

# Set the wiping bounds (min and max x, y)
min_x = spill_position[0] - half_length_x
max_x = spill_position[0] + half_length_x
min_y = spill_position[1] - half_length_y
max_y = spill_position[1] + half_length_y

# Use downward-facing orientation for wiping: (0, 0, 1, 0) in wxyz
down_quaternion = np.array([0, 0, 1, 0])

# Wipe in a grid pattern with small overlapping strokes to avoid large motions
num_strokes = 5
x_positions = np.linspace(min_x, max_x, num_strokes)
y_positions = np.linspace(min_y, max_y, num_strokes)

# Start at a safe height above the table before wiping
safe_z = 0.1
goto_pose(np.array([spill_position[0], spill_position[1], safe_z]), down_quaternion)

# Move down to wiping height (z = 0.0)
goto_pose(np.array([spill_position[0], spill_position[1], 0.0]), down_quaternion)

# Perform back-and-forth wiping motions in a grid
for y in y_positions:
    for i, x in enumerate(x_positions):
        # Alternate direction for back-and-forth motion
        if i % 2 == 1:
            x = x_positions[-(i+1)]
        goto_pose(np.array([x, y, 0.0]), down_quaternion)

# Return to safe height after wiping
goto_pose(np.array([spill_position[0], spill_position[1], safe_z]), down_quaternion)