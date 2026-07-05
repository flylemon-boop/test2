import numpy as np

# Get poses and extents of the red and green cubes
red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube (we need both position and quaternion)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before approaching
open_gripper()

# Approach and grasp the red cube with z_approach=0.1
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift the red cube to a safe height (at least +0.2m in Z from current position)
safe_z = grasp_pos[2] + 0.2
lifted_position = np.array([grasp_pos[0], grasp_pos[1], safe_z])
goto_pose(lifted_position, grasp_quat)  # No z_approach needed when moving in free space

# Compute the placement position on top of the green cube
place_z = green_center[2] + green_extent[2]/2 + red_extent[2]/2
place_pos = np.array([green_center[0], green_center[1], place_z])

# Move laterally above the green cube, then approach downward using z_approach=0.1
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()

# Optionally lift the gripper slightly after release to avoid collision
final_lift = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.1])
goto_pose(final_lift, grasp_quat)