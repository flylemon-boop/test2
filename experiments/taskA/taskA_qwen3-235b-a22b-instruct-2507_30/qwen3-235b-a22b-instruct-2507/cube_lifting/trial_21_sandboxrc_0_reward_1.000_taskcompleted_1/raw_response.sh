import numpy as np

# Get the grasp pose for the red cube
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

# Approach the red cube from above by adding a z offset
z_approach_distance = 0.1  # 10 cm approach distance

# Move to the approach pose above the grasp position
goto_pose(grasp_position, grasp_quaternion, z_approach=z_approach_distance)

# Move down to the actual grasp pose (no need to specify z_approach again)
goto_pose(grasp_position, grasp_quaternion)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube by moving upward in z-axis
lift_distance = 0.2  # Lift 20 cm
lifted_position = grasp_position + np.array([0, 0, lift_distance])

# Lift the cube without any additional approach since we are already at the grasp pose
goto_pose(lifted_position, grasp_quaternion)