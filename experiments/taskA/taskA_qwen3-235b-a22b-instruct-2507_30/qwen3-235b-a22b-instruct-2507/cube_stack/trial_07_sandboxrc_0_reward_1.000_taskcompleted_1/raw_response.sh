import numpy as np

# Get poses and extents of the red and green cubes
red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

# Approach the red cube with z_approach for controlled descent
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)

# Grasp the red cube
close_gripper()

# Lift the red cube to a safe height
safe_height = grasp_position[2] + 0.2
lift_position = np.array([grasp_position[0], grasp_position[1], safe_height])
goto_pose(lift_position, grasp_quaternion)

# Compute the stacking height for placing on the green cube
place_z = green_center[2] + green_extent[2]/2 + red_extent[2]/2
place_position = np.array([green_center[0], green_center[1], place_z])

# Move to above the green cube with approach motion
goto_pose(place_position, grasp_quaternion, z_approach=0.1)

# Release the red cube
open_gripper()

# Lift slightly after release to avoid collision
final_lift_position = np.array([place_position[0], place_position[1], place_position[2] + 0.1])
goto_pose(final_lift_position, grasp_quaternion)