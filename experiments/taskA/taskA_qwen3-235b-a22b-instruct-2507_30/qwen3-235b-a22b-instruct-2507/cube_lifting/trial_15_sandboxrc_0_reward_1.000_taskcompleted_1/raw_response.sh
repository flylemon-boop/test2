import numpy as np

# Get the grasp pose for the red cube to ensure proper orientation
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

# Approach the red cube from above with a z_approach of 0.1 meters
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube by moving upward in the z-axis by 0.2 meters
lifted_position = grasp_position + np.array([0.0, 0.0, 0.2])
goto_pose(lifted_position, grasp_quaternion)