# Code block 0
import numpy as np

# First, lift both arms slightly to avoid occlusion
initial_pose0 = get_arm0_gripper_pose()
initial_pose1 = get_arm1_gripper_pose()

# Define a safe height offset (e.g. 10 cm) for initial lift
safe_z_offset = 0.1

# Lift arm0 and arm1 slightly in z-direction
lifted_pos0 = initial_pose0[0] + np.array([0, 0, safe_z_offset])
lifted_pos1 = initial_pose1[0] + np.array([0, 0, safe_z_offset])

# Use current orientations during the lift
goto_pose_both(lifted_pos0, initial_pose0[1], lifted_pos1, initial_pose1[1])

# Detect handle positions after lifting
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Desired gripper orientation: sideways grasp with gripper y-axis aligned to world z-axis
# This means the gripper should face horizontally toward the handle
# Target orientation: x-axis forward (into handle), y-axis up (aligned with world z), z-axis left/right
# Corresponds to quaternion [w, x, y, z] = [0.5**0.5, 0, 0, 0.5**0.5] -> 90-degree rotation around x-axis from default
sideways_quat = np.array([np.sqrt(0.5), 0, 0, np.sqrt(0.5)])  # w, x, y, z

# Approach distance in z-direction (before final grasp)
approach_distance = 0.05  # 5 cm above the target for safer approach

# Prepare target poses for grasping
target_pos0 = handle0_pos.copy()
target_pos1 = handle1_pos.copy()

# We adjust approach: move in the direction perpendicular to the handle's position relative to center
# Since pot is centered and handles are on opposite sides, we can infer approach direction from handle position
# Assume table center is approximately [0.6, 0, 0.02] or similar, but we can compute direction from symmetry
center_x = (handle0_pos[0] + handle1_pos[0]) / 2
center_y = (handle0_pos[1] + handle1_pos[1]) / 2
center_pos = np.array([center_x, center_y, handle0_pos[2]])

# Direction from handle0 to center (arm0 approaches from outside to inside)
approach_dir0 = (center_pos - handle0_pos)
approach_dir0 = approach_dir0 / np.linalg.norm(approach_dir0)  # normalize

# Direction from handle1 to center (arm1 approaches from opposite side)
approach_dir1 = (center_pos - handle1_pos)
approach_dir1 = approach_dir1 / np.linalg.norm(approach_dir1)  # normalize

# Compute pre-grasp positions by stepping back along approach direction
pre_grasp0 = handle0_pos + approach_dir0 * 0.1
pre_grasp1 = handle1_pos + approach_dir1 * 0.1

# Move both arms to pre-grasp positions with sideways orientation
goto_pose_both(pre_grasp0, sideways_quat, pre_grasp1, sideways_quat)

# Now perform precise grasp with z_approach to ensure smooth descent into grasp
# We use z_approach = 0.05 so it goes 5cm above then moves down precisely
goto_pose_both(handle0_pos, sideways_quat, handle1_pos, sideways_quat, z_approach=0.05)

# Close both grippers simultaneously to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift both arms vertically to raise the pot
lift_height = 0.1  # lift pot by 10 cm
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

# Maintain the same orientation during lift
goto_pose_both(final_pos0, sideways_quat, final_pos1, sideways_quat)