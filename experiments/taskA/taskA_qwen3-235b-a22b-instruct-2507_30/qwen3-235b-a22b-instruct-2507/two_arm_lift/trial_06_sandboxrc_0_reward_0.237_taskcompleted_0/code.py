# Code block 0
import numpy as np

# First, lift both arms slightly to avoid occlusion
initial_pose0 = get_arm0_gripper_pose()
initial_pose1 = get_arm1_gripper_pose()

lift_offset = np.array([0.0, 0.0, 0.1])
lifted_pos0 = initial_pose0[0] + lift_offset
lifted_pos1 = initial_pose1[0] + lift_offset

goto_pose_both(lifted_pos0, initial_pose0[1], lifted_pos1, initial_pose1[1])

# Get handle positions using vision detection
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation with gripper y-axis aligned to world z-axis
# This corresponds to a quaternion that represents a 90-degree rotation around the x-axis
# which gives us [cos(45°), sin(45°), 0, 0] = [0.707, 0.707, 0, 0] in wxyz
sideways_quat_wxyz = np.array([0.707, 0.707, 0, 0])  # Rotate 90° around x-axis

# For arm0 (on one side), approach from the side
approach_offset0 = np.array([-0.1, 0, 0])  # Approach along negative x
target_pos0 = handle0_pos + approach_offset0

# For arm1 (opposite side), approach from the other side
approach_offset1 = np.array([0.1, 0, 0])   # Approach along positive x
target_pos1 = handle1_pos + approach_offset1

# Simultaneously approach both handles with z_approach for precision
z_approach = 0.05
goto_pose_both(
    target_pos0, sideways_quat_wxyz,
    target_pos1, sideways_quat_wxyz,
    z_approach=z_approach
)

# Move to final grasp positions without z-approach now
goto_pose_both(
    handle0_pos, sideways_quat_wxyz,
    handle1_pos, sideways_quat_wxyz
)

# Close both grippers simultaneously to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift the pot up by same height using both arms
lift_height = 0.1
final_lift_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_lift_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(
    final_lift_pos0, sideways_quat_wxyz,
    final_lift_pos1, sideways_quat_wxyz
)