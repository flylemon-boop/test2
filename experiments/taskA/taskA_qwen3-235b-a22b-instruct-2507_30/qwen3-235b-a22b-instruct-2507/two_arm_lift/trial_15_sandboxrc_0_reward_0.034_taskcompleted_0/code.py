# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
initial_pose0 = get_arm0_gripper_pose()
initial_pose1 = get_arm1_gripper_pose()

# Lift both arms up by 10 cm initially
lift_offset = np.array([0.0, 0.0, 0.1])
lifted_pos0 = initial_pose0[0] + lift_offset
lifted_pos1 = initial_pose1[0] + lift_offset

goto_pose_both(lifted_pos0, initial_pose0[1], lifted_pos1, initial_pose1[1])

# Get current handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis
# This avoids top-down grasp (which would be [0,0,1,0]) and uses a side approach.
# Target quaternion represents rotation from gripper frame to world frame such that:
# - Gripper's y-axis points upward (aligned with world z)
# Achieved by rotating 90 degrees around x-axis: quaternion [cos(45°), sin(45°), 0, 0] -> [√2/2, √2/2, 0, 0]
sideways_quat = np.array([np.sqrt(2)/2, np.sqrt(2)/2, 0, 0])  # w, x, y, z

# Prepare approach: come in 5 cm from the side along the horizontal plane
approach_dist = 0.05

# For arm 0 (grasping handle 0): approach from the negative x direction of the handle
approach_dir0 = np.array([-1.0, 0.0, 0.0])
approach_pos0 = handle0_pos + approach_dir0 * approach_dist

# For arm 1 (grasping handle 1): approach from the positive x direction of the handle
approach_dir1 = np.array([1.0, 0.0, 0.0])
approach_pos1 = handle1_pos + approach_dir1 * approach_dist

# Move both arms to approach poses
goto_pose_both(approach_pos0, sideways_quat, approach_pos1, sideways_quat)

# Now perform precise grasp with small z-approach (downward motion for side grasp)
# Use z_approach=0.05 so it first goes 5cm above target, then moves down
goto_pose_both(handle0_pos, sideways_quat, handle1_pos, sideways_quat, z_approach=0.05)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift both arms simultaneously to raise the pot
lift_height = 0.1  # Lift 10 cm up
final_pos0 = handle0_pos + np.array([0.0, 0.0, lift_height])
final_pos1 = handle1_pos + np.array([0.0, 0.0, lift_height])

# Lift both arms to final position
goto_pose_both(final_pos0, sideways_quat, final_pos1, sideways_quat)