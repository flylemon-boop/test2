# Code block 0
import numpy as np

# Get the position and extent of the brown spill
spill_position, _, spill_extent = get_object_pose("brown spill", return_bbox_extent=True)

# Define the wiping orientation (downward-facing)
wiping_orientation = np.array([0, 0, 1, 0])  # wxyz

# Compute the bounds for wiping based on the spill's position and extent
half_extent_x = spill_extent[0] / 2
half_extent_y = spill_extent[1] / 2

min_x = spill_position[0] - half_extent_x
max_x = spill_position[0] + half_extent_x
min_y = spill_position[1] - half_extent_y
max_y = spill_position[1] + half_extent_y

# Define a small step size to avoid large motions between IK solutions
step_size = 0.05

# Start from slightly above the table to ensure safe approach
approach_height = 0.02
safe_approach_position = np.array([spill_position[0], spill_position[1], approach_height])
goto_pose(safe_approach_position, wiping_orientation)

# Move down to the table surface (z = 0.0) for wiping
table_surface_position = np.array([spill_position[0], spill_position[1], 0.0])
goto_pose(table_surface_position, wiping_orientation)

# Perform back-and-forth wiping motions along the x-axis within the spill bounds
current_x = min_x
direction = 1  # 1 for forward, -1 for backward

while current_x <= max_x and current_x >= min_x:
    # Wipe horizontally at current y-level
    target_position = np.array([current_x, min_y, 0.0])
    goto_pose(target_position, wiping_orientation)
    
    # Move across in steps along x
    next_x = current_x + direction * step_size
    if next_x > max_x or next_x < min_x:
        # Reverse direction when hitting the boundary and move up in y
        direction *= -1
        min_y += step_size
        if min_y > max_y:
            break  # Stop if we've covered all y regions
    else:
        current_x = next_x

# Final pose after wiping is complete
final_position = np.array([spill_position[0], spill_position[1], approach_height])
goto_pose(final_position, wiping_orientation)