import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
pos0_lift = np.array([0.5, -0.3, 0.3])
quat0 = np.array([1.0, 0.0, 0.0, 0.0])  # Placeholder identity quaternion
pos1_lift = np.array([0.5, 0.3, 0.3])
quat1 = np.array([1.0, 0.0, 0.0, 0.0])  # Placeholder identity quaternion
goto_pose_both(pos0_lift, quat0, pos1_lift, quat1)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Desired sideways grasp orientation: gripper y-axis aligned with world z-axis
# This corresponds to a rotation of 90 degrees around the x-axis -> quaternion [cos(45°), sin(45°), 0, 0]
# Which is approximately [0.707, 0.707, 0, 0] in wxyz format
sideways_quat = np.array([0.707, 0.707, 0.0, 0.0])

# Prepare approach: lift slightly above each handle
approach_offset = 0.05
handle0_approach = handle0_pos + np.array([0, 0, approach_offset])
handle1_approach = handle1_pos + np.array([0, 0, approach_offset])

# Move both arms above their respective handles
goto_pose_both(handle0_approach, sideways_quat, handle1_approach, sideways_quat)

# Open both grippers before grasping
open_gripper_arm0()
open_gripper_arm1()

# Lower both arms to grasp the handles using z_approach mechanism (negative offset)
goto_pose_both(handle0_pos, sideways_quat, handle1_pos, sideways_quat, z_approach=-0.05)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms simultaneously to raise the pot to a higher position
lift_height = 0.15
lifted_handle0_pos = handle0_pos + np.array([0, 0, lift_height])
lifted_handle1_pos = handle1_pos + np.array([0, 0, lift_height])

# Perform coordinated lift
goto_pose_both(lifted_handle0_pos, sideways_quat, lifted_handle1_pos, sideways_quat)