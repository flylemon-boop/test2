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
lift_height = 0.15  # Lift to 15 cm above table (within required 0.15–0.20 m range)
lift_pos_arm0 = hammer_pos + np.array([0, 0, lift_height - hammer_pos[2]])

# Ensure z is within bounds
lift_z = max(0.15, min(lift_height, 0.20))
lift_pos_arm0[2] = lift_z

goto_pose_arm0(lift_pos_arm0, q_arm0_approach)

# Step 3: Plan handover position near the midpoint between initial gripper positions
# Initial rough positions
arm0_init_x = 0.44
arm1_init_x = 1.18
mid_x = (arm0_init_x + arm1_init_x) / 2.0  # Midpoint in X

# Handover at mid_x, same y as original hammer, z within 0.15–0.20
handover_pos = np.array([mid_x, hammer_pos[1], lift_z])

# But first, Arm0 must rotate the hammer so that Arm1 can grasp the handle safely.
# Since hammer handle is toward +Y and head toward -Y, and Arm1 is on the right,
# Arm0 should rotate the hammer 180 degrees around Z so the handle points toward Arm1 (-X direction).
# However, since Arm1 grasps the handle, it needs access to the middle of the handle.
# So instead, Arm0 moves to midpoint with hammer upright, then orients for transfer.

# Move Arm0 to handover position
goto_pose_arm0(handover_pos, q_arm0_approach)

# Step 4: Arm1 moves to handover position to receive the hammer
# It must approach from its side, but avoid collision — use z_approach
approach_pos_arm1 = handover_pos + np.array([0, 0, z_offset])
goto_pose_arm1(approach_pos_arm1, q_arm1_grasp, z_approach=0.0)

# Now descend carefully to grasp position
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=-z_offset)

# Step 5: Open Arm0 gripper to release the hammer
open_gripper_arm0()

# Step 6: Close Arm1 gripper to grasp the hammer handle
close_gripper_arm1()

# Final check: keep z in valid range during handover — already enforced by lift_z

# Task complete: handover finished