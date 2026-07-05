# Code block 0
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

# Before moving, orient hammer appropriately for transfer
# We rotate the hammer 90 degrees around Z so that when Arm1 grasps it from +X side,
# it grabs the handle along its length (handle toward +Y, head toward -Y), opening along Y
# This requires rotating the end-effector by 90 degrees (quaternion for +90 deg around Z)
# Rotation of +90 deg around Z-axis: w=cos(45°), z=sin(45°) => [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])
q_handover_orientation = q_rotate_z_90  # After rotation, gripper opens along new direction

# Move Arm0 to handover position with rotated orientation
goto_pose_arm0(handover_pos, q_handover_orientation)

# Step 4: Arm1 moves to grasp the handle at handover point
# Since the hammer handle is now oriented along Y, Arm1 should approach from the +X side
# So it needs to have gripper opening along Y-axis, facing down: [0, 0, 1, 0]
# Approach from 8cm (0.08m) further in X to avoid collision
approach_offset_arm1 = 0.08
approach_pos_arm1 = handover_pos + np.array([approach_offset_arm1, 0, 0])

# Move Arm1 to approach position (from the right/X+ side)
goto_pose_arm1(approach_pos_arm1, q_arm1_grasp, z_approach=0.0)

# Move vertically down to handover height without additional z_approach since already approached
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=-abs(approach_pos_arm1[0] - handover_pos[0]))

# Now close Arm1 gripper to grasp the hammer handle
close_gripper_arm1()

# Step 5: Arm0 releases the hammer
open_gripper_arm0()

# Final check: Arm1 lifts slightly to confirm grasp
final_lift_pos = handover_pos + np.array([0, 0, 0.05])
goto_pose_arm1(final_lift_pos, q_arm1_grasp)