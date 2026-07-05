import numpy as np

# First, lift both arms slightly to avoid occlusion
initial_pose0 = get_arm0_gripper_pose()
initial_pose1 = get_arm1_gripper_pose()

# Slight upward offset in Z to clear the table
lift_offset = 0.1
lifted_pos0 = initial_pose0[0] + np.array([0, 0, lift_offset])
lifted_pos1 = initial_pose1[0] + np.array([0, 0, lift_offset])

# Move both arms up simultaneously to a safe height
goto_pose_both(lifted_pos0, initial_pose0[1], lifted_pos1, initial_pose1[1])

# Get current positions of the two handles via vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis (preferred)
# This corresponds to a quaternion that represents a 90-degree rotation around the x-axis
# from the default [0,0,1,0] top-down orientation to a horizontal side grasp.
# The desired orientation has gripper frame: x forward, y down, z left/right depending on arm
# For both arms, we want the gripper's y-axis aligned with world z-axis -> use quaternion [sqrt(2)/2, 0, 0, sqrt(2)/2] (i.e., 90 deg around x)
sideways_quat = np.array([np.sqrt(2)/2, 0, 0, np.sqrt(2)/2])  # w, x, y, z

# Approach distance in Z for safer grasp (approach from above by 5cm)
approach_height = 0.05

# Prepare poses for grasping
# Arm 0 approaches handle 0
grasp_pos0 = handle0_pos.copy()
grasp_pos0[2] += approach_height  # approach from above

# Arm 1 approaches handle 1
grasp_pos1 = handle1_pos.copy()
grasp_pos1[2] += approach_height  # approach from above

# Simultaneously move both arms to approach position above their respective handles
goto_pose_both(grasp_pos0, sideways_quat, grasp_pos1, sideways_quat, z_approach=approach_height)

# Now perform the actual grasp by closing both grippers
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms simultaneously to lift the pot
lift_height = 0.1  # lift 10 cm above grasp point
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

# Move both arms up together to lift the pot
goto_pose_both(final_pos0, sideways_quat, final_pos1, sideways_quat)