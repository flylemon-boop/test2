import numpy as np

# Get poses and extents of the red and green cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube (to get correct orientation)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before grasping
open_gripper()

# Approach the red cube with z_approach for controlled descent
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift the red cube to a safe height
safe_z = red_pos[2] + 0.2
lift_pos = np.array([red_pos[0], red_pos[1], safe_z])
goto_pose(lift_pos, grasp_quat)

# Compute the stacking placement position on top of the green cube
place_z = green_pos[2] + green_extent[2]/2 + red_extent[2]/2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally above the green cube, then approach downward with z_approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()