# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

# Lift arms up by 0.1 meters in Z to clear the workspace
lifted_pos0 = pos0.copy()
lifted_pos0[2] += 0.1
lifted_pos1 = pos1.copy()
lifted_pos1[2] += 0.1

goto_pose_both(lifted_pos0, quat0, lifted_pos1, quat1)

# Get current handle positions from vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis
# Desired gripper forward direction (x-axis) points toward handle center
# We want the gripper's y-axis (lateral) to align with world z-axis (up)
# This corresponds to a rotation of 90 degrees around x-axis from default [0,0,1,0]
# Resulting quaternion is approximately [0.707, 0, 0, 0.707] for 90 deg around x

sideways_quat = np.array([0.707, 0, 0, 0.707])  # w,x,y,z -> matches WXYZ format

# Approach distance in Z for pre-grasp pose
approach_distance = 0.05

# Pre-grasp: move above the handle position with sideways orientation and approach from side
pre_grasp_offset0 = np.array([0, 0, approach_distance])
pre_grasp_pos0 = handle0_pos + pre_grasp_offset0

pre_grasp_offset1 = np.array([0, 0, approach_distance])
pre_grasp_pos1 = handle1_pos + pre_grasp_offset1

# Move both arms simultaneously to pre-grasp poses
goto_pose_both(pre_grasp_pos0, sideways_quat, pre_grasp_pos1, sideways_quat)

# Now go directly to grasp poses without additional z_approach since we're already approaching from side
# Use z_approach=0.0 here because we control the motion manually
goto_pose_both(handle0_pos, sideways_quat, handle1_pos, sideways_quat, z_approach=0.0)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Slightly lift both arms together to raise the pot
lift_height = 0.1
final_pos0 = handle0_pos.copy()
final_pos0[2] += lift_height
final_pos1 = handle1_pos.copy()
final_pos1[2] += lift_height

goto_pose_both(final_pos0, sideways_quat, final_pos1, sideways_quat)