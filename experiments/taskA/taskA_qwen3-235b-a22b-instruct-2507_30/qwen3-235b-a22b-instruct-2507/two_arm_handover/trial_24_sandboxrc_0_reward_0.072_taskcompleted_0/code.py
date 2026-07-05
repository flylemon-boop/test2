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
# However, since Arm1 grasps the handle, it needs access to the handle end.

# Instead: Arm0 moves to midpoint and presents the hammer horizontally with handle pointing toward Arm1 (+X direction)
# So Arm0 keeps orientation with gripper opening along Y, but now translates to midpoint.

goto_pose_arm0(handover_pos, q_arm0_approach)

# Step 4: Arm1 moves to grasp the handle at handover point
# Arm1 needs to move to the handle end — which is now at handover_pos, but the handle extends backward from Arm0's grip
# Since Arm0 is gripping the middle of the handle, the handle end is displaced by half the handle length in the direction away from the head.

# We don't know exact handle length, but we know it's between 0.15 and 0.25m.
# Assume average 0.2m → half is 0.1m. Direction: since hammer was aligned Y, and we rotated?
# Actually, we did not rotate — we kept the same orientation. So handle is still along Y?

# Wait: we need to reorient the hammer so Arm1 can reach without collision.

# Better strategy:
# After lifting, Arm0 rotates the hammer so that the handle points toward Arm1 (along +X), with hammer head behind.
# So final orientation: hammer lies along X-axis, handle toward +X, head toward -X.
# Then Arm0 moves to midpoint, and Arm1 approaches from the right (+X side) to grasp the handle end.

# New plan:
# After lifting, Arm0 rotates hammer to align along X-axis (handle to +X)
# Rotation: 90 degrees around Z-axis (from Y-aligned to X-aligned)
# Quat for 90 deg CCW around Z: [cos(45°), 0, 0, sin(45°)] = [0.707, 0, 0, 0.707]
q_rotate_x = np.array([0.707, 0, 0, 0.707])  # Rotate so gripper opens along X, which makes hammer along X

# But we want handle to +X — when Arm0 grips the middle and rotates, if we use this quat, the gripper will face X.
# And since the handle was originally toward +Y, rotating 90 deg CCW around Z makes +Y → +X → so handle goes to +X. Good.

# Rotate hammer to X-alignment
goto_pose_arm0(lift_pos_arm0, q_rotate_x)

# Now move to handover position at mid_x, same y, safe z
# The handle now extends from grip point backward along -X (toward head) and forward along +X (handle end)
# So the full handle end is at: handover_pos + (0.1, 0, 0) approximately (half-length in +X)

# Set handover position so that the handle center is at mid_x, but we'll let Arm1 grasp the end

# Move Arm0 to place the *gripped point* (middle of handle) at x = mid_x - 0.1? No.
# We want the handle end to be accessible to Arm1 at ~mid_x.
# So place the middle at: mid_x - (half_handle_length)
# Use approx 0.1 m for half length
half_handle = 0.1
handle_end_pos = np.array([mid_x, hammer_pos[1], lift_z])
middle_pos_for_handover = handle_end_pos - np.array([half_handle, 0, 0])

# Move Arm0 to this position
goto_pose_arm0(middle_pos_for_handover, q_rotate_x)

# Now Arm1 moves to grasp the handle end at handle_end_pos
# Arm1 needs to approach from the right (positive X side), so approach along -X direction

# Set Arm1 grasp orientation: gripper opening along Y-axis, facing down — [0,0,1,0]
# But to grasp the handle end, which is along X, Arm1 should have gripper opening along X-axis?
# Wait: gripper opening direction is the direction between fingers.

# If the handle is along X, then to grasp it, the gripper should open along X — so fingers close along Y.
# But our reference says:
#   Arm1 gripper facing down opening along Y-axis: [0,0,1,0]
# So opening along X would be different.

# A quaternion where gripper opens along X and faces down: requires rotation.
# From Arm0's initial: [0,0.707,0.707,0] -> opening along X, facing down.
# But for Arm1, we need the same orientation relative to world? 
# Actually, the coordinate system is shared (robot0 frame). So same quat applies.

# So for Arm1 to open along X (fingers moving in Y), we use: [0, 0.707, 0.707, 0]

q_arm1_open_x = np.array([0, 0.707, 0.707, 0])

# But we need to grasp the end of the handle — so Arm1 should move to handle_end_pos, but approach from the side?

# Better: approach from above with z_approach to avoid collision.

# First, go above the target
approach_pos_arm1 = handle_end_pos + np.array([0, 0, 0.1])

goto_pose_arm1(approach_pos_arm1, q_arm1_open_x, z_approach=0.0)

# Then descend vertically to grasp
goto_pose_arm1(handle_end_pos, q_arm1_open_x, z_approach=-0.1)

# Close gripper to grasp the handle end
close_gripper_arm1()

# Step 5: Arm0 releases after Arm1 has secured the grip
open_gripper_arm0()

# Optional: Arm0 retracts slightly to avoid interference
retract_pos = middle_pos_for_handover + np.array([-0.05, 0, 0])  # Move left a bit
goto_pose_arm0(retract_pos, q_rotate_x)

# Task complete