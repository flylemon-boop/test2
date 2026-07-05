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
pre_grasp_offset = np.array([0, 0, 0.1])
goto_pose_arm0(hammer_pos + pre_grasp_offset, q_arm0_grasp, z_approach=0.0)

# Then perform precise approach directly above
goto_pose_arm0(hammer_pos, q_arm0_grasp, z_approach=safe_z_above_table)

# Close Arm0's gripper to grasp the hammer
close_gripper_arm0()

# Step 2: Lift hammer to a safe height for transport
lift_height = 0.18  # Within required 0.15-0.20 range
lifted_pos = np.array([hammer_pos[0], hammer_pos[1], lift_height])
goto_pose_arm0(lifted_pos, q_arm0_grasp)

# Step 3: Move toward handover zone near midpoint between arms
# Midpoint in x: roughly average of Arm0 and Arm1 starting x positions
mid_x = (0.44 + 1.18) / 2.0
handover_x = mid_x
handover_y = 0.0  # Keep near centerline

# Desired handover position — keep z within bounds
handover_pos = np.array([handover_x, handover_y, lift_height])

# But we cannot just move directly — need to avoid collisions
# First raise slightly if needed, then move laterally, then lower
high_clearance_pos = np.array([lifted_pos[0], lifted_pos[1], 0.3])
goto_pose_arm0(high_clearance_pos, q_arm0_grasp)

# Now move horizontally toward handover zone
goto_pose_arm0(np.array([handover_pos[0], handover_pos[1], 0.3]), q_arm0_grasp)

# Now descend to handover height with approach safety
goto_pose_arm0(handover_pos, q_arm1_grasp, z_approach=safe_z_above_table)

# At this point, Arm0 is holding the hammer at handover location with orientation suitable for Arm1

# Step 4: Prepare Arm1 to receive the hammer

# First, open gripper and go to a safe waiting position above the handover point
arm1_wait_pos = np.array([handover_pos[0], handover_pos[1], 0.3])
goto_pose_arm1(arm1_wait_pos, q_arm1_grasp)

# Descend to just above handover height
receive_pos = np.array([handover_pos[0], handover_pos[1], lift_height + 0.02])  # Slightly higher than hammer
goto_pose_arm1(receive_pos, q_arm1_grasp, z_approach=safe_z_above_table)

# Now Arm1 descends precisely to grasp the handle
final_receive_pos = np.array([handover_pos[0], handover_pos[1], lift_height])
goto_pose_arm1(final_receive_pos, q_arm1_grasp, z_approach=safe_z_above_table)

# Close Arm1 gripper to grasp the hammer handle
close_gripper_arm1()

# Step 5: Arm0 releases after confirmation of grasp
# Wait briefly to ensure grip (in real system might check force, but here we assume timing)
open_gripper_arm0()

# Optional: Arm0 retracts safely upward
retract_pos = np.array([handover_pos[0], handover_pos[1], 0.3])
goto_pose_arm0(retract_pos, q_arm0_grasp)

# Success condition met: hammer handed over at correct z height