# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
initial_lift_height = 0.1
_, quat0 = get_arm0_gripper_pose()
_, quat1 = get_arm1_gripper_pose()
pos0_initial_lift = np.array([0.4, 0.0, 0.5])  # High safe position for arm0
pos1_initial_lift = np.array([0.4, 0.0, 0.5])  # High safe position for arm1 (mirrored)

goto_pose_both(pos0_initial_lift, quat0, pos1_initial_lift, quat1, z_approach=0.0)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis
# This corresponds to a quaternion that represents a 90-degree rotation around x-axis from default [0,0,1,0]
# Desired orientation: x forward, y down, z left (for side grasp), so we want to avoid top-down
# Use quaternion for 90 degree rotation about x-axis: cos(45) + sin(45)*i -> [0.707, 0.707, 0, 0]
side_grasp_quat = np.array([0.707, 0.707, 0.0, 0.0])

# Prepare approach poses with z_offset for precise grasping
z_approach = 0.05  # Approach from 5cm above

# Move both arms simultaneously to approach the handles
goto_pose_both(
    handle0_pos + np.array([0, 0, z_approach]), side_grasp_quat,
    handle1_pos + np.array([0, 0, z_approach]), side_grasp_quat,
    z_approach=0.0
)

# Descend to grasp pose
goto_pose_both(
    handle0_pos, side_grasp_quat,
    handle1_pos, side_grasp_quat,
    z_approach=z_approach  # Internal approach handling
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms synchronously to same height to lift the pot
lift_height = 0.2  # Lift 20cm up
lift_pose0 = handle0_pos + np.array([0, 0, lift_height])
lift_pose1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(lift_pose0, side_grasp_quat, lift_pose1, side_grasp_quat, z_approach=0.0)