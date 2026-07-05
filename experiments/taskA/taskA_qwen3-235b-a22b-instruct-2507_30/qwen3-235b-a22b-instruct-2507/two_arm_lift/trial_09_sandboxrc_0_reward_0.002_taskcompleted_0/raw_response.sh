import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0_lift = np.array([0.5, -0.3, 0.3])
quat0_lift = np.array([1, 0, 0, 0])  # Placeholder orientation, will be updated
pos1_lift = np.array([0.5, 0.3, 0.3])
quat1_lift = np.array([1, 0, 0, 0])

goto_pose_both(pos0_lift, quat0_lift, pos1_lift, quat1_lift)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientations: gripper y-axis aligned with world z-axis
# This means the gripper will approach from the side, not top-down
# Desired gripper orientation: rotation of 90 degrees around x-axis -> quaternion [cos(45°), sin(45°), 0, 0]
# which is approximately [0.707, 0.707, 0, 0] for a roll to face sideways vertically
gripper_quat_sideways = np.array([0.707, 0.707, 0, 0])  # w, x, y, z

# Prepare approach: first move above the handle with z_approach
z_approach = 0.05  # 5 cm above before grasping

# Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach poses simultaneously
goto_pose_both(
    handle0_pos, gripper_quat_sideways,
    handle1_pos, gripper_quat_sideways,
    z_approach=z_approach
)

# Now perform the grasp without z_approach (move down to actual handle)
goto_pose_both(
    handle0_pos, gripper_quat_sideways,
    handle1_pos, gripper_quat_sideways
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms up together to same height
lift_offset = np.array([0, 0, 0.1])  # Lift 10 cm up
target_height0 = handle0_pos + lift_offset
target_height1 = handle1_pos + lift_offset

goto_pose_both(
    target_height0, gripper_quat_sideways,
    target_height1, gripper_quat_sideways
)