# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

lift_height = 0.1  # Lift 10 cm up
pos0_lifted = pos0.copy()
pos0_lifted[2] += lift_height
pos1_lifted = pos1.copy()
pos1_lifted[2] += lift_height

goto_pose_both(pos0_lifted, quat0, pos1_lifted, quat1, z_approach=0.0)

# Get handle positions from vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: y-axis of gripper aligned with world z-axis
# This means the gripper will approach horizontally, not top-down
# Desired rotation: align gripper forward (usually -Z) toward the handle, and gripper Y with world Z
# Target quaternion for sideways grasp (gripper frame): X right, Y up (world Z), Z forward (pointing into handle)
# We want a quaternion that represents a 90-degree rotation around X-axis from default [0,0,1,0] to make Y point up
# Rotation of 90 degrees around X-axis: quaternion [cos(45°), sin(45°), 0, 0] -> [√2/2, √2/2, 0, 0]
sideways_quat = np.array([np.sqrt(2)/2, np.sqrt(2)/2, 0, 0])  # wxyz

# Approach distance in Z (before grasping)
approach_dist = 0.05  # 5 cm approach

# Move both arms to approach pose simultaneously
goto_pose_both(
    position0=handle0_pos,
    quaternion_wxyz0=sideways_quat,
    position1=handle1_pos,
    quaternion_wxyz1=sideways_quat,
    z_approach=approach_dist
)

# Now move to final grasp pose (without approach)
goto_pose_both(
    position0=handle0_pos,
    quaternion_wxyz0=sideways_quat,
    position1=handle1_pos,
    quaternion_wxyz1=sideways_quat,
    z_approach=0.0
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift the pot: compute lift target (raise both handles by same amount)
lift_amount = 0.1  # Lift 10 cm
target_height0 = handle0_pos + np.array([0, 0, lift_amount])
target_height1 = handle1_pos + np.array([0, 0, lift_amount])

# Lift both arms simultaneously to lift the pot
goto_pose_both(
    position0=target_height0,
    quaternion_wxyz0=sideways_quat,
    position1=target_height1,
    quaternion_wxyz1=sideways_quat,
    z_approach=0.0
)