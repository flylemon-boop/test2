import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0_init, quat0_init = get_arm0_gripper_pose()
pos1_init, quat1_init = get_arm1_gripper_pose()

lift_height = 0.1  # Lift arms by 10 cm initially
pos0_lifted = pos0_init + np.array([0, 0, lift_height])
pos1_lifted = pos1_init + np.array([0, 0, lift_height])

goto_pose_both(pos0_lifted, quat0_init, pos1_lifted, quat1_init)

# Get current handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: y-axis of gripper aligned with world z-axis
# This means the gripper will approach horizontally, not from top
# Desired rotation: align gripper forward (usually -z) toward the handle, and gripper y with world z
# We use a fixed quaternion that represents this orientation
# For Franka gripper, to have the fingers horizontal (y along world z), we can use a 90-degree rotation around x-axis
# That would be quaternion [cos(45°), sin(45°), 0, 0] -> approx [0.707, 0.707, 0, 0]
sideways_quat = np.array([0.707, 0.707, 0, 0])  # w, x, y, z

# Approach distance for z_approach to prevent collision
approach_distance = 0.05  # 5 cm above grasp point

# Prepare arm 0 to grasp handle 0
# Move to approach pose first, then go to exact grasp
grasp_offset0 = np.array([-0.05, 0, 0])  # adjust x to reach handle from side
target_pos0 = handle0_pos + grasp_offset0

# Prepare arm 1 to grasp handle 1
grasp_offset1 = np.array([0.05, 0, 0])  # opposite x direction
target_pos1 = handle1_pos + grasp_offset1

# Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# Move both arms simultaneously to approach position
goto_pose_both(
    target_pos0,
    sideways_quat,
    target_pos1,
    sideways_quat,
    z_approach=approach_distance
)

# Now perform the actual grasp motion (insertion along z_approach path)
goto_pose_both(
    target_pos0,
    sideways_quat,
    target_pos1,
    sideways_quat,
    z_approach=0.0
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms simultaneously to raise the pot
lift_amount = 0.1  # Lift pot by 10 cm
lifted_pos0 = target_pos0 + np.array([0, 0, lift_amount])
lifted_pos1 = target_pos1 + np.array([0, 0, lift_amount])

goto_pose_both(lifted_pos0, sideways_quat, lifted_pos1, sideways_quat)

# Final coordination: ensure both arms are at same height and stable
# Task complete