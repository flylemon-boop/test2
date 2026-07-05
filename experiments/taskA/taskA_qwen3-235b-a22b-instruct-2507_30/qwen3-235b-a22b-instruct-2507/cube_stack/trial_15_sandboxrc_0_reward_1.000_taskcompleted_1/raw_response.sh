import numpy as np

# Get poses and extents of red and green cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube (for position and reliable quaternion)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach the red cube with z_approach=0.1 for grasping
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Perform the grasp
open_gripper()
goto_pose(grasp_pos, grasp_quat)  # Final descent without z_approach
close_gripper()

# Lift the red cube to a safe height
safe_height = grasp_pos[2] + 0.2
lift_pos = np.array([grasp_pos[0], grasp_pos[1], safe_height])
goto_pose(lift_pos, grasp_quat)

# Compute stacking position on top of the green cube
place_z = green_pos[2] + green_extent[2]/2 + red_extent[2]/2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally above the green cube with approach height
approach_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.1])
goto_pose(approach_pos, grasp_quat)

# Place the red cube using controlled descent with z_approach=0.1
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Optionally lift up slightly after release
final_lift_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.1])
goto_pose(final_lift_pos, grasp_quat)