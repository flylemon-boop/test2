# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

lift_offset = 0.1  # 10 cm lift
pos0_lifted = pos0 + np.array([0, 0, lift_offset])
pos1_lifted = pos1 + np.array([0, 0, lift_offset])

goto_pose_both(pos0_lifted, quat0, pos1_lifted, quat1)

# Get handle positions from vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis (preferred)
# This corresponds to a rotation that aligns the gripper laterally
# Example: For a sideways grasp, we can use a quaternion that represents 90-degree rotation around x-axis
# Such that the gripper faces inward toward the pot, with its y-axis pointing up (aligned with world z)
sideways_quat = np.array([np.sqrt(2)/2, -np.sqrt(2)/2, 0, 0])  # wxyz: rotation around x by -90 degrees

# Approach distance in Z for controlled grasping
approach_dist = 0.05  # 5 cm approach

# Move both arms to grasp poses simultaneously
goto_pose_both(
    position0=handle0_pos,
    quaternion_wxyz0=sideways_quat,
    position1=handle1_pos,
    quaternion_wxyz1=sideways_quat,
    z_approach=approach_dist
)

# Close both grippers simultaneously to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift the pot to a desired height (e.g., 0.15 meters above current handle positions)
lift_height = 0.15
target_lift0 = handle0_pos + np.array([0, 0, lift_height])
target_lift1 = handle1_pos + np.array([0, 0, lift_height])

# Lift both arms together to raise the pot
goto_pose_both(
    position0=target_lift0,
    quaternion_wxyz0=sideways_quat,
    position1=target_lift1,
    quaternion_wxyz1=sideways_quat
)