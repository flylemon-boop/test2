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
# And then reorient the gripper to present the handle vertically with opening along Y for Arm1

# But Arm0 cannot directly hand over in final orientation — instead, we hold it horizontally
# Best strategy: keep hammer horizontal during transfer, then let Arm1 adjust.

# Final presentation pose: hammer at handover point, oriented so handle extends along +X toward Arm1
# So Arm1 can approach from +X side, grasp handle along X direction? 
# But Arm1 expects gripper opening along Y-axis -> so hammer must have its long axis along Y

# Therefore: after picking up, Arm0 must rotate the hammer 90 degrees around Z so that handle points along +Y
# Wait — no! The hammer is already along Y. Original: handle toward +Y, head toward -Y.
# So if Arm0 picks up at handle (middle of handle), and lifts, the handle is already extending forward (+Y).
# But Arm1 is on the right (positive X). So to hand over, Arm0 should rotate the hammer 90 degrees around Z-axis clockwise (so handle points right, +X)
# Then Arm1 can grasp the handle along X? But Arm1’s gripper opens along Y.

# Problem: Arm1 gripper opens along Y-axis → so to grasp the handle, the handle must be aligned along Y-axis.

# Therefore: hammer must remain aligned along Y-axis during handover.

# Correct plan:
# - Arm0 picks up at handle (middle of handle), lifts it, keeps it aligned along Y
# - Moves to midline (x ~ 0.81), maintains y near initial y, z = 0.18
# - Rotates its wrist so that when it releases, the hammer remains stable
# - Arm1 approaches from the right (+X side), but must grasp the hammer **along Y-axis**, meaning its gripper will clamp across the handle width (X-direction pinch)
#   → This is fine as long as the handle is within reach

# However, Arm1’s gripper opens along Y → jaws move in Y direction → so it grips objects by squeezing along Y → requires object extent along Y
# So yes, Arm1 can grasp the hammer handle (which extends along Y) by closing jaws along Y

# So we do NOT need to rotate the hammer. It stays along Y.

# But Arm0 must avoid colliding with Arm1. So it should not go too far right.

# Revised handover position: x = ~0.81, y = same as before, z = 0.18

# We are already at handover_position with correct orientation.

# Ensure orientation still matches expected grasp
goto_pose_arm0(handover_position, q_arm0_grasp)

# Step 4: Prepare Arm1 to grasp at handover location
# Arm1 needs to approach from its side, so compute target grasp position on hammer handle
# We want Arm1 to grasp the *same* point (middle of handle), but from the other side

# So target position for Arm1 is same as current hammer position
arm1_target_pos = handover_position.copy()

# Arm1 needs to approach with gripper opening along Y-axis, facing down
# Use z_approach to carefully insert
goto_pose_arm1(arm1_target_pos + np.array([0.1, 0, 0.1]), q_arm1_grasp)
goto_pose_arm1(arm1_target_pos, q_arm1_grasp, z_approach=0.05)

# Close Arm1's gripper to grasp the handle
close_gripper_arm1()

# Step 5: Arm0 releases only after Arm1 has secured the grip
open_gripper_arm0()

# Optional: move Arm0 away safely
safe_retract_pos = handover_position + np.array([-0.2, 0, 0.1])
goto_pose_arm0(safe_retract_pos, q_arm0_grasp)

# Task complete: handover occurred at z=0.18 ∈ [0.15, 0.20], and Arm1 holds the hammer handle