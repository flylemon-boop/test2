# Code block 0
import numpy as np

# Get poses and extents of the red and green cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open the gripper before grasping
open_gripper()

# Approach the red cube with z_approach for controlled descent
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube to a safe height
safe_height = grasp_pos[2] + 0.2
lifted_pos = np.array([grasp_pos[0], grasp_pos[1], safe_height])
goto_pose(lifted_pos, grasp_quat)

# Compute the placement position on top of the green cube
place_z = green_pos[2] + green_extent[2]/2 + red_extent[2]/2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally above the green cube with approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()