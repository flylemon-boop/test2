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
lift_height = 0.15  # Ensure hammer is lifted safely
lifted_pos_arm0 = hammer_pos + np.array([0, 0, lift_height])
goto_pose_arm0(lifted_pos_arm0, q_arm0_approach)

# Step 3: Plan handover location — midpoint between arms in x, same y, and z in valid range
# Approximate initial gripper positions
arm0_x_init = 0.44
arm1_x_init = 1.18
mid_x = (arm0_x_init + arm1_x_init) / 2.0
handover_y = hammer_pos[1]  # Keep same y to minimize lateral motion
handover_z = 0.18  # Within required 0.15–0.20 range

handover_pos = np.array([mid_x, handover_y, handover_z])

# Rotate the hammer so that when Arm1 grasps the handle, it's oriented properly
# After pickup, hammer head is at -Y relative to handle center. So when transferring,
# Arm1 must approach from the side or front/back depending on orientation.
# We rotate the hammer 90 degrees around Z so that handle is aligned with X-axis
# This allows Arm1 to approach along Y safely.

# Rotation: 90 degrees around Z-axis (from Y-aligned to X-aligned)
# Quaternion for 90 deg CCW rotation around Z: [cos(45°), 0, 0, sin(45°)] = [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])

# First orient hammer before moving to handover point
goto_pose_arm0(handover_pos, q_rotate_z_90 @ q_arm0_approach @ q_rotate_z_90**-1, z_approach=0.0)

# Now move to handover position with rotated hammer
goto_pose_arm0(handover_pos, q_rotate_z_90 @ q_arm0_approach @ q_rotate_z_90**-1)

# Step 4: Arm1 moves to grasp the handle at handover position
# Since hammer is now rotated, handle extends along X, so Arm1 can approach along Y
# We approach from +Y side to avoid collision

approach_offset_arm1 = 0.1  # 10 cm approach distance along Y
approach_pos_arm1 = handover_pos + np.array([0, approach_offset_arm1, 0])

# Move Arm1 above handover point with approach from Y
goto_pose_arm1(approach_pos_arm1, q_arm1_grasp, z_approach=0.0)

# Descend to handover height
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=-approach_offset_arm1)

# Open gripper before grasp
open_gripper_arm1()

# Final descent to grasp
goto_pose_arm1(handover_pos, q_arm1_grasp)

# Close gripper to secure hammer
close_gripper_arm1()

# Step 5: Arm0 releases and retracts
open_gripper_arm0()

# Retract Arm0 vertically to avoid collision
retract_pos_arm0 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm0(retract_pos_arm0, q_rotate_z_90 @ q_arm0_approach @ q_rotate_z_90**-1)

# Success: Handover complete within required z-range