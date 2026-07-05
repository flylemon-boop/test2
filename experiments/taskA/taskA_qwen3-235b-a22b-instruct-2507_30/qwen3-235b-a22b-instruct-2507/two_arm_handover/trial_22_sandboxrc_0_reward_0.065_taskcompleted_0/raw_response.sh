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

# Step 1: Arm0 moves above the hammer with safe z_approach
safe_z_above_table = 0.1  # We'll use this to approach without collision

# Lift a bit higher first to ensure clearance during motion
goto_pose_arm0(hammer_pos + np.array([0, 0, 0.2]), q_arm0_grasp)

# Approach the hammer from above with small z_approach for precision
goto_pose_arm0(hammer_pos, q_arm0_grasp, z_approach=safe_z_above_table)

# Close Arm0's gripper to grasp the hammer handle
close_gripper_arm0()

# Step 2: Lift the hammer to a safe height (within required 0.15–0.20 m range)
lift_height = 0.18  # Within valid range and allows clearance
hammer_lifted_pos = hammer_pos.copy()
hammer_lifted_pos[2] = lift_height
goto_pose_arm0(hammer_lifted_pos, q_arm0_grasp)

# Step 3: Move hammer toward midline for handover
# Compute approximate midpoint between arms in x-direction
mid_x = (0.44 + 1.18) / 2  # Approximately 0.81
handover_x = mid_x
handover_y = hammer_lifted_pos[1]  # Keep same y (aligned along Y-axis originally)
handover_z = 0.18  # Maintain within required range

handover_position = np.array([handover_x, handover_y, handover_z])

# Before moving, consider rotating the hammer gradually so Arm1 can take over
# First move laterally to handover x-position while keeping orientation suitable for transfer
goto_pose_arm0(handover_position, q_arm0_grasp)

# Now, slowly rotate the hammer so that its handle is oriented appropriately for Arm1
# The hammer should be rotated such that the handle points toward Arm1 and is aligned with Y-axis
# Since the original hammer lies along Y-axis (handle toward +Y), and Arm1 is on the right (higher x),
# we need to rotate it around Z-axis by -90 degrees so that the handle is now pointing toward +X (toward Arm1)
# And then reorient the gripper to make it easier for Arm1 to grasp

# New orientation: Rotate base frame by -90° around Z-axis → affects how the gripper holds it
# But instead of complex rotation, we will change orientation so that the hammer is now held vertically?
# No — requirement: Arm1 must grasp the *handle*, not the head. So we keep it horizontal.

# Instead, rotate the hammer 90 degrees around Z so that the handle now points in +X direction (toward Arm1)
# And set gripper orientation accordingly so that when released, Arm1 can grab from the side (along Y)

# Use a new quaternion for final handover orientation: 
# We want the hammer along X-axis, handle toward +X, and gripper still facing down but opening along Y
# This matches Arm1's expected grasp direction

# Let’s define a new target orientation: gripper opens along Y (like Arm1 default), facing down
q_handover_orientation = np.array([0, 0, 1, 0])  # WXYZ: down, opening along Y

# Perform gradual orientation change at handover point
goto_pose_arm0(handover_position, q_handover_orientation)

# Step 4: Prepare Arm1 to receive the hammer

# Estimate where the handle will be when hammer is at handover position with current orientation
# Since the hammer handle was at `hammer_pos` initially and we're now holding it at handover_position,
# and assuming the hammer length is L, with head at one end and handle at other.

# But note: get_hammer_pose() returns middle of handle.
# So total hammer length unknown, but handle length ∈ [0.15, 0.25]
# We assume full hammer length ≈ 2×handle_length? Not exactly — problem says "handle length"

# Actually: "hammer handle length is randomized between 0.15m and 0.25m"
# And hammer lies flat, aligned along Y-axis, handle toward +Y.

# So from center of handle, the farthest point of handle is +Y direction.
# When we rotate the hammer 90° CCW around Z (from Arm0 perspective), the handle will point toward +X.

# Therefore, after rotation, the handle extends from handover_position in +X direction.
# So Arm1 should approach from the +Y or -Y side? But gripper opens along Y.

# Since Arm1 gripper opens along Y-axis, it needs to grasp perpendicular to Y.
# So Arm1 should come from ±Y direction and close along Y.

# Best: Arm1 approaches from +Y side (forward) to avoid table gap?

# But handover happens at midline. Let's compute Arm1's approach position.

# We want Arm1 to reach to a position near the handle tip, which is:
# handle_tip_offset = + (estimated_handle_length) * [1, 0, 0] since now pointing +X
estimated_handle_length = 0.20  # Midpoint of 0.15–0.25
handle_grasp_pos_relative_to_mid = estimated_handle_length / 2  # Grasp halfway along handle

# After rotation, handle extends in +X from current handover_position
handle_grasp_pos = handover_position + np.array([handle_grasp_pos_relative_to_mid, 0, 0])

# Arm1 needs to approach this position from +Y or -Y?
# Prefer +Y (positive Y) to stay clear of Arm0 and central gap

approach_offset_y = 0.15  # Come from front (positive Y) with buffer
grip_z = 0.18  # Same height

# Arm1 approach start: well away in Y, then descend
arm1_approach_start = handle_grasp_pos + np.array([0, approach_offset_y, 0.1])
arm1_final_grasp_pos = handle_grasp_pos + np.array([0, 0, 0])  # At correct height

# Move Arm1 above the grasp location
goto_pose_arm1(arm1_approach_start, q_arm1_grasp)

# Descend vertically to grasp position with z_approach
goto_pose_arm1(arm1_final_grasp_pos, q_arm1_grasp, z_approach=0.1)

# Step 5: Synchronized handover — open Arm0, close Arm1

# Ensure Arm0 is ready to release
# Double-check position
goto_pose_arm0(handover_position, q_handover_orientation)  # Final confirmation

# Open Arm0 gripper to release hammer
open_gripper_arm0()

# Immediately close Arm1 gripper to grasp the handle
close_gripper_arm1()

# Optional: Arm1 lifts slightly to confirm grasp
lift_check = arm1_final_grasp_pos + np.array([0, 0, 0.05])
goto_pose_arm1(lift_check, q_arm1_grasp)

# Task complete