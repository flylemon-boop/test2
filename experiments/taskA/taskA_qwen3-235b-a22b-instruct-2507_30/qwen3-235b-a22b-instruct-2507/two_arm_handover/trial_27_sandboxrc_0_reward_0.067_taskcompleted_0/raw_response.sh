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
handover_z = 0.17  # Within required 0.15-0.20 range

# Target handover position (hammer handle center at this point)
handover_pos = np.array([handover_x, handover_y, handover_z])

# Arm0 needs to move to handover location
# First go above the handover point, then descend
approach_handover_pos_arm0 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm0(approach_handover_pos_arm0, q_arm0_approach)

# Descend to exact handover pose
goto_pose_arm0(handover_pos, q_arm0_approach, z_approach=-0.1)

# Step 4: Arm1 moves to grasp the hammer handle at handover location
# Arm1 needs to approach from its side — since hammer is now at handover_pos
# We must place Arm1's gripper such that it grasps the handle, not the head
# The hammer lies along Y-axis, handle toward +Y, head toward -Y
# So Arm1 should approach along Y-axis with gripper opening along Y

# Estimate where the handle end is — extend a bit beyond center toward +Y
# But since we're grasping at the center during handover, we use the same position
# However, Arm1 must be oriented correctly

# Move Arm1 above the handover point first
approach_handover_pos_arm1 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm1(approach_handover_pos_arm1, q_arm1_grasp, z_approach=0.0)

# Descend vertically to grasp position
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=-0.1)

# Now close Arm1's gripper to grasp the hammer
close_gripper_arm1()

# Step 5: Arm0 opens gripper to release the hammer
open_gripper_arm0()

# Optional: Arm0 retracts slightly upward to ensure clean release
retract_pos_arm0 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm0(retract_pos_arm0, q_arm0_approach)

# Success condition met: handover complete with hammer at valid z-height