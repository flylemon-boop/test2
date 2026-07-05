import numpy as np

# Get the grasp pose for the red cube
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

# Approach the red cube from 10 cm above
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)

# Move down to the grasp pose
goto_pose(grasp_position, grasp_quaternion)

# Close the gripper to pick up the red cube
close_gripper()

# Lift the red cube by moving up 20 cm along Z-axis
lift_position = grasp_position + np.array([0, 0, 0.2])
goto_pose(lift_position, grasp_quaternion)