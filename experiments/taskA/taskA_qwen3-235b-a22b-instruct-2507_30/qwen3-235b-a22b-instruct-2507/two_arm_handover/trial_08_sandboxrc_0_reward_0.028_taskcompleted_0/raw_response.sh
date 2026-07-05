import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get hammer handle pose
hammer_pos, hammer_quat = get_hammer_pose()

# Define useful quaternions for orientation
# Arm0: Gripper facing down, opening along X-axis (for grasping hammer handle from top)
q_arm0_grasp = np.array([0, 0.707, 0.707, 0])  # WXYZ

# For handover, we want hammer to be held vertically with handle up and head down
# So that Arm1 can grasp the handle from the side
q_handover_vertical = np.array([0, 1, 0, 0])  # WXYZ, gripper opening along Y-axis

# Step 1: Arm0 moves above hammer with approach
approach_offset = 0.1  # 10 cm above for safe approach
hover_pos = hammer_pos + np.array([0, 0, approach_offset])

goto_pose_arm0(hover_pos, q_arm0_grasp)

# Move down to grasp pose with z_approach
goto_pose_arm0(hammer_pos, q_arm0_grasp, z_approach=0.02)

# Close gripper to grasp hammer
close_gripper_arm0()

# Step 2: Lift hammer to a safe height within z = [0.15, 0.20]
lift_height = 0.18  # Within required range
lift_pos = np.array([hammer_pos[0], hammer_pos[1], lift_height])

goto_pose_arm0(lift_pos, q_arm0_grasp)

# Step 3: Rotate hammer to vertical orientation (handle up) for handover
# We now rotate in place to orient the hammer vertically so that handle is up
goto_pose_arm0(lift_pos, q_handover_vertical)

# Step 4: Plan handover location near midpoint between arms
# Approximate midpoint based on initial arm positions
mid_x = (0.44 + 1.18) / 2.0  # ~0.81 m
handover_x = mid_x
handover_y = 0.0  # Keep near centerline
handover_z = 0.18  # Within required 0.15–0.20 range

handover_pos = np.array([handover_x, handover_y, handover_z])

# Move Arm0 to handover position at constant height
goto_pose_arm0(handover_pos, q_handover_vertical)

# Step 5: Arm1 moves to grasp the hammer handle
# Since hammer is vertical with handle up, Arm1 should approach horizontally along Y-axis
# from the front (positive Y) or back? Let's assume front (positive Y) is safer.

# Estimate current handle tip position when hammer is vertical
# Handle length is unknown but between 0.15 and 0.25; use conservative estimate
# When hammer is vertical and held at middle of handle, handle extends half-length up and down
# But we lifted from middle, so after rotating vertical, the handle extends upward.
# We want Arm1 to grasp the lower part of the handle, near where Arm0 is holding.

# So Arm1 should go to same x,y as handover_pos but slightly behind (negative y) to avoid collision
arm1_approach_offset = -0.15  # 15 cm behind in Y
arm1_grasp_y = handover_pos[1] + arm1_approach_offset
arm1_grasp_pos = np.array([handover_pos[0], arm1_grasp_y, handover_pos[2]])

# Orientation: Arm1 gripper opening along Y-axis (facing forward), so it can grab from behind
q_arm1_grasp = np.array([0, 0, 1, 0])  # WXYZ, opening along Y

# Move Arm1 above grasp point first to avoid collision
hover_arm1 = arm1_grasp_pos + np.array([0, 0, 0.1])
goto_pose_arm1(hover_arm1, q_arm1_grasp)

# Move down to approach level
goto_pose_arm1(arm1_grasp_pos, q_arm1_grasp, z_approach=0.02)

# Open gripper just before grasp (though already open, ensure)
open_gripper_arm1()

# Now close gripper to grasp hammer handle
close_gripper_arm1()

# Step 6: Arm0 opens gripper to release hammer
open_gripper_arm0()

# Optional: Arm0 retracts slightly upward to clear
retract_pos = handover_pos + np.array([0, 0, 0.05])
goto_pose_arm0(retract_pos, q_handover_vertical)