import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0_lift = np.array([0.4, -0.2, 0.3])
quat0_lift = np.array([1, 0, 0, 0])  # Default orientation
pos1_lift = np.array([0.4, 0.2, 0.3])
quat1_lift = np.array([1, 0, 0, 0])

goto_pose_both(pos0_lift, quat0_lift, pos1_lift, quat1_lift)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientations: gripper y-axis aligned with world z-axis
# This corresponds to a rotation of 90 degrees around the x-axis from default
# Resulting quaternion for such rotation: w=0.707, x=0.707, y=0, z=0 (approx)
sideways_quat = np.array([np.sqrt(0.5), np.sqrt(0.5), 0, 0])

# Approach from side: use z_approach to first come in higher, then move down
z_approach = 0.1

# Open both grippers before grasping
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach the handles from the side with z offset
goto_pose_both(
    handle0_pos + np.array([0, 0, z_approach]), sideways_quat,
    handle1_pos + np.array([0, 0, z_approach]), sideways_quat,
    z_approach=0.0  # We already added the offset manually
)

# Now lower to grasp position
goto_pose_both(
    handle0_pos, sideways_quat,
    handle1_pos, sideways_quat,
    z_approach=0.0
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms simultaneously to same height
lift_height = 0.2  # 20 cm up from current position
lift_offset = np.array([0, 0, lift_height])

goto_pose_both(
    handle0_pos + lift_offset, sideways_quat,
    handle1_pos + lift_offset, sideways_quat,
    z_approach=0.0
)