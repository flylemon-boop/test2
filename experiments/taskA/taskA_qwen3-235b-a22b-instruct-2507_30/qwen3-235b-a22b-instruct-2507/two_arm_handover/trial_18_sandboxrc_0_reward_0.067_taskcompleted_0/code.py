# Code block 0
import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get hammer handle pose
hammer_pos, hammer_quat = get_hammer_pose()

# Define useful quaternions for orientation
# Arm0: Gripper facing down, opening along X-axis (for grasping hammer handle from top)
q_arm0_grasp = np.array([0, 0.707, 0.707, 0])  # WXYZ

# For handover, we want to rotate the hammer so that Arm1 can grasp the handle
# Arm1 needs gripper opening along Y-axis, facing down
q_arm1_grasp = np.array([0, 0, 1, 0])  # WXYZ

# Step 1: Arm0 moves above the hammer with safe z-approach
z_approach_height = 0.1  # 10 cm above target for approach
pre_grasp_offset_z = 0.15  # Lift hammer by this amount after grasp

# Move Arm0 above the hammer for approach
goto_pose_arm0(hammer_pos + np.array([0, 0, z_approach_height]), q_arm0_grasp, z_approach=0.0)

# Lower to grasp position and close gripper
goto_pose_arm0(hammer_pos, q_arm0_grasp, z_approach=z_approach_height)
close_gripper_arm0()

# Lift hammer slightly to clear table
lift_pos = hammer_pos + np.array([0, 0, pre_grasp_offset_z])
goto_pose_arm0(lift_pos, q_arm0_grasp)

# Step 2: Plan handover location near midpoint between arms
# Approximate midpoint in x-direction
mid_x = (0.44 + 1.18) / 2.0
handover_y = 0.0  # Keep near center in y
handover_z = 0.175  # Midway in allowed range [0.15, 0.20]

handover_position = np.array([mid_x, handover_y, handover_z])

# Ensure hammer is oriented correctly for handover:
# - Hammer handle should be aligned along Y-axis (handle toward +Y, head toward -Y)
# - We need to reorient so Arm1 can grasp the handle without collision

# First, move Arm0 to handover position while rotating the hammer gradually
# Intermediate waypoint to avoid swinging
intermediate_position = np.array([mid_x, 0, 0.3])  # High arc to avoid collisions
goto_pose_arm0(intermediate_position, q_arm0_grasp)

# Now descend to handover height with hammer rotated so handle is accessible to Arm1
# We'll keep the same orientation for now and let Arm1 adjust its grasp

goto_pose_arm0(handover_position, q_arm0_grasp)

# Step 3: Arm1 moves to grasp the hammer handle
# Estimate handle position: since hammer lies along Y-axis, handle is at +Y direction from center
# Handle length is between 0.15 and 0.25, assume worst case ~0.2m
handle_grasp_offset = 0.18  # Estimated distance from center to handle middle
arm1_approach_pos = handover_position + np.array([0, handle_grasp_offset + 0.1, 0.1])  # Approach from +Y side

# Move Arm1 above the expected handle position
goto_pose_arm1(arm1_approach_pos, q_arm1_grasp, z_approach=0.0)

# Descend to grasp position
handle_grasp_pos = handover_position + np.array([0, handle_grasp_offset, 0])
goto_pose_arm1(handle_grasp_pos, q_arm1_grasp, z_approach=0.1)

# Close gripper on handle
close_gripper_arm1()

# Step 4: Arm0 releases after Arm1 has secure grasp
open_gripper_arm0()

# Final check: ensure hammer z is within bounds during handover
# Since we maintained handover_position.z = 0.175 throughout, it's valid

# Task complete