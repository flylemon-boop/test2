import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get the current hammer pose (middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Constants
HANDOVER_Z_MIN = 0.15
HANDOVER_Z_MAX = 0.20
APPROACH_HEIGHT = 0.1  # Approach from above to avoid collision
BUFFER = 0.08  # 8cm buffer between grippers
TABLE_CLEARANCE = 0.02  # Slight lift above table

# Compute approximate handover location: midpoint between initial arm positions
# Based on rough initial positions: Arm0 at (0.44, 0.0), Arm1 at (1.18, 0.0)
handover_x = (0.44 + 1.18) / 2.0
handover_y = 0.0
handover_z = (HANDOVER_Z_MIN + HANDOVER_Z_MAX) / 2.0  # Midpoint in allowed range

handover_position = np.array([handover_x, handover_y, handover_z])

# Define quaternions for orientation
# Arm0 will approach hammer initially with gripper along X-axis (facing down)
gripper_down_x = np.array([0, 0.707, 0.707, 0])  # WXYZ
# For Y-axis opening downward
gripper_down_y = np.array([0, 1, 0, 0])  # WXYZ for Arm0
gripper_down_y_arm1 = np.array([0, 0, 1, 0])  # WXYZ for Arm1

# Step 1: Arm0 moves above the hammer to prepare for grasping
approach_pos_arm0 = hammer_pos.copy()
approach_pos_arm0[2] += APPROACH_HEIGHT  # Move above hammer

goto_pose_arm0(approach_pos_arm0, gripper_down_x)
# Descend to grasp position
goto_pose_arm0(hammer_pos, gripper_down_x, z_approach=-APPROACH_HEIGHT)

# Close gripper to grasp hammer
close_gripper_arm0()

# Step 2: Lift hammer slightly
lift_pos = hammer_pos.copy()
lift_pos[2] += TABLE_CLEARANCE
goto_pose_arm0(lift_pos, gripper_down_x)

# Step 3: Move hammer to handover position
# First move up to safe height
safe_height_pos = lift_pos.copy()
safe_height_pos[2] = max(HANDOVER_Z_MAX, safe_height_pos[2] + 0.1)
goto_pose_arm0(safe_height_pos, gripper_down_x)

# Then move laterally to handover position
handover_safe = handover_position.copy()
handover_safe[2] = safe_height_pos[2]
goto_pose_arm0(handover_safe, gripper_down_x)

# Then descend to final handover height
goto_pose_arm0(handover_position, gripper_down_x, z_approach=safe_height_pos[2]-handover_position[2])

# Ensure hammer z is within required bounds during handover
if not (HANDOVER_Z_MIN <= handover_position[2] <= HANDOVER_Z_MAX):
    raise RuntimeError("Handover z-value out of bounds")

# Step 4: Arm1 moves to grasp hammer handle
# Move Arm1 above handover point first
approach_handover_arm1 = handover_position.copy()
approach_handover_arm1[2] += APPROACH_HEIGHT

goto_pose_arm1(approach_handover_arm1, gripper_down_y_arm1)

# Descend to grasp position
goto_pose_arm1(handover_position, gripper_down_y_arm1, z_approach=-APPROACH_HEIGHT)

# Close gripper to grasp hammer handle
close_gripper_arm1()

# Step 5: Arm0 releases and retracts
open_gripper_arm0()

# Retract Arm0 vertically to avoid collision
retract_pos = handover_position.copy()
retract_pos[2] += APPROACH_HEIGHT
goto_pose_arm0(retract_pos, gripper_down_x)

# Optional: Lift Arm1 slightly after taking over
lift_final = handover_position.copy()
lift_final[2] += TABLE_CLEARANCE
goto_pose_arm1(lift_final, gripper_down_y_arm1)