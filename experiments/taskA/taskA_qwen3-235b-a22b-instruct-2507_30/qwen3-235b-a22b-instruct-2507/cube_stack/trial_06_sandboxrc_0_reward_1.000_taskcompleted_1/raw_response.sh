import numpy as np

# Get poses and extents for red and green cubes
red_pose, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pose, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach the red cube with z_approach to prepare for grasping
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Move down to grasp position (controlled descent)
goto_pose(grasp_pos, grasp_quat)

# Close gripper to grasp the red cube
close_gripper()

# Lift red cube to a safe height
safe_height = grasp_pos[2] + 0.2
lift_position = np.array([grasp_pos[0], grasp_pos[1], safe_height])
goto_pose(lift_position, grasp_quat)

# Compute stacking position on top of green cube
place_z = green_pose[2] + green_extent[2]/2 + red_extent[2]/2
stack_position = np.array([green_pose[0], green_pose[1], place_z])

# Move laterally above the green cube with approach height
approach_position = np.array([green_pose[0], green_pose[1], stack_position[2] + 0.1])
goto_pose(approach_position, grasp_quat)

# Place the red cube on the green cube with controlled descent
goto_pose(stack_position, grasp_quat, z_approach=0.1)

# Open gripper to release the red cube
open_gripper()