import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get the current hammer pose (middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Define key quaternions for orientation control
# Arm0 will approach the hammer with gripper opening along Y-axis (facing down)
q_arm0_approach = np.array([0, 1, 0, 0])  # [0, 1, 0, 0] for Y-axis opening, facing down
# For handover, we want Arm1 to grasp the handle — so gripper should open along Y-axis, facing down
q_arm1_grasp = np.array([0, 0, 1, 0])  # [0, 0, 1, 0] for Arm1, opening along Y-axis

# Step 1: Arm0 moves above the hammer for safe approach
z_offset = 0.1  # 10 cm above hammer for safe descent
approach_pos_arm0 = hammer_pos + np.array([0, 0, z_offset])

# Move Arm0 above the hammer with z_approach to ensure vertical descent
goto_pose_arm0(approach_pos_arm0, q_arm0_approach, z_approach=0.0)

# Descend vertically to grasp the hammer handle
goto_pose_arm0(hammer_pos, q_arm0_approach, z_approach=-z_offset)

# Close gripper to grasp the hammer
close_gripper_arm0()

# Step 2: Lift the hammer to a safe height
lift_height = 0.15  # Ensure hammer is lifted to at least 0.15m above table
lifted_pos_arm0 = hammer_pos + np.array([0, 0, lift_height])
goto_pose_arm0(lifted_pos_arm0, q_arm0_approach)

# Step 3: Plan handover location near midpoint between initial arm positions
# Approximate midpoint in X between Arm0 and Arm1 (in robot0's frame)
mid_x = (0.44 + 1.18) / 2
handover_x = mid_x
handover_y = 0.0  # Keep around y=0 to avoid table gap
handover_z = 0.175  # Midpoint within required 0.15–0.20 range

# Compute handover position
handover_pos = np.array([handover_x, handover_y, handover_z])

# Before moving, orient hammer appropriately for transfer:
# We want to rotate the hammer 180 degrees around Z so that handle points toward Arm1 (+X direction)
# Current hammer alignment: handle toward +Y, head toward -Y
# After pickup by Arm0: gripper faces down, opening along Y -> holding handle along Y
# To hand over properly, we need to rotate so handle points toward Arm1 (positive X)

# Rotate the hammer 90 degrees counterclockwise around Z so handle points +X
# This means rotating the gripper orientation so it now opens along X-axis
q_rotate_z_90 = np.array([np.cos(np.pi/4), 0, 0, np.sin(np.pi/4)])  # 90 deg CCW around Z
q_rotated = q_rotate_z_90  # Not directly composable this way; instead use known quaternion

# Instead, define new orientation: after 90 deg CCW Z rotation, original Y becomes X
# So gripper opening direction becomes X → use [0, 0.707, 0.707, 0] for opening along X
q_arm0_rotate = np.array([0, 0.707, 0.707, 0])

# First move to rotated orientation at current location (no translation)
goto_pose_arm0(lifted_pos_arm0, q_arm0_rotate)

# Now move laterally toward handover position
goto_pose_arm0(handover_pos, q_arm0_rotate)

# Step 4: Arm1 moves to grasp the handle at handover point
# Since handle now points +X, and Arm1 is on the right, Arm1 needs to approach from the side (+X direction)
# So Arm1 should have gripper opening along Y-axis (facing down), approaching along X

# Position Arm1 gripper at handover point, but slightly offset in X to approach
approach_offset_arm1 = -0.08  # Stay 8cm away initially to avoid collision
arm1_approach_pos = handover_pos + np.array([approach_offset_arm1, 0, 0])

# Move Arm1 to approach position with correct orientation
goto_pose_arm1(arm1_approach_pos, q_arm1_grasp)

# Move forward slowly to final grasp position
final_grasp_offset = 0.01  # Final insertion motion
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=-final_grasp_offset)

# Close Arm1 gripper to grasp handle
close_gripper_arm1()

# Step 5: Arm0 releases and retracts
open_gripper_arm0()

# Retract Arm0 safely upward and backward
retract_pos_arm0 = handover_pos + np.array([0, -0.1, 0.1])
goto_pose_arm0(retract_pos_arm0, q_arm0_rotate)

# Task complete