import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get hammer pose (middle of the handle)
hammer_pos, hammer_quat = get_hammer_pose()

# Define safe approach height above table for grasping
safe_lift_z = 0.15  # z-value we want to maintain during handover
approach_distance = 0.08  # 8 cm approach distance from above

# Arm0 picks up the hammer first
# Since hammer lies flat on table along Y-axis with handle toward +Y and head toward -Y,
# Arm0 will grasp the handle end (so move slightly behind the middle point in -Y direction)

# Compute handle tip position for Arm0 grasp
handle_length_min = 0.15
handle_length_max = 0.25
# We don't know exact handle length but we know the middle is at hammer_pos
# So handle end (where Arm0 should grasp) is approximately: hammer_pos - (estimated half_handle) * [0,1,0]
half_handle_est = (handle_length_min + handle_length_max) / 2 * 0.5  # ~0.1 m
handle_grasp_pos = hammer_pos.copy()
handle_grasp_pos[1] -= half_handle_est  # move back in Y to reach handle tip

# But since we only have middle of handle pose, use that as best estimate if uncertain
# Instead, just use middle of handle as grasp point for robustness
grasp_point_arm0 = hammer_pos.copy()

# Orientation for Arm0: gripper facing down, opening along X-axis → [0, 0.707, 0.707, 0]
quat_arm0_down_x = np.array([0, 0.707, 0.707, 0])

# Approach from above to avoid collision
goto_pose_arm0(grasp_point_arm0, quat_arm0_down_x, z_approach=approach_distance)

# Move down to grasp
goto_pose_arm0(grasp_point_arm0, quat_arm0_down_x)

# Close gripper to grasp hammer
close_gripper_arm0()

# Now lift the hammer to safe height for handover (z between 0.15 and 0.20)
lifted_hammer_pos = grasp_point_arm0.copy()
lifted_hammer_pos[2] = safe_lift_z

goto_pose_arm0(lifted_hammer_pos, quat_arm0_down_x)

# Prepare for handover: determine handover location near midpoint between arms
# Approximate initial gripper x-positions
arm0_start_x = 0.44
arm1_start_x = 1.18
midpoint_x = (arm0_start_x + arm1_start_x) / 2.0  # ~0.81 m

# Set handover position at this midpoint in x, same y as original, correct z
handover_pos = lifted_hammer_pos.copy()
handover_pos[0] = midpoint_x

# Ensure z remains within required bounds
if handover_pos[2] < 0.15:
    handover_pos[2] = 0.15
elif handover_pos[2] > 0.20:
    handover_pos[2] = 0.20

# Before moving Arm0 to handover point, ensure no collisions
# Move Arm0 smoothly to handover position
goto_pose_arm0(handover_pos, quat_arm0_down_x)

# Now prepare Arm1 to receive the hammer
# Arm1 needs to grasp the **handle**, so it should approach from below or side?
# But gripper can only open along certain directions.

# Reference: Arm1 gripper facing down opening along Y-axis: [0, 0, 1, 0]
# So fingers extend along ±Y. To grasp the handle (which is along Y), Arm1 should have gripper oriented so that opening aligns with Y-axis.

# Desired orientation for Arm1: gripper facing down, opening along Y → [0, 0, 1, 0]
quat_arm1_down_y = np.array([0, 0, 1, 0])

# Grasp point on handle for Arm1: same as current hammer middle/handle center?
# But Arm0 is holding one end (handle tip), so the other part of the handle is free.
# We assume after lifting, the hammer is horizontal, held vertically by Arm0 at handle tip.

# For smooth handover, Arm1 should grasp the handle closer to the head side? No — goal says "grasp the hammer handle (not hammer head)"
# So anywhere on the handle except the head is acceptable.

# Best: Arm1 moves to a point on the handle between middle and where Arm0 is gripping? But Arm0 is at far end.

# Instead, let Arm1 approach the middle of the handle for grasp.
receive_pos = hammer_pos.copy()
receive_pos[0] = midpoint_x  # move to midline
receive_pos[2] = handover_pos[2]  # same height

# First, approach from a safe offset to avoid collision
approach_offset_arm1 = 0.1  # 10 cm forward (+Y) to approach from front
approach_pos_arm1 = receive_pos.copy()
approach_pos_arm1[1] += approach_offset_arm1  # come from +Y direction
approach_pos_arm1[2] += 0.05  # slightly higher to avoid bumping

goto_pose_arm1(approach_pos_arm1, quat_arm1_down_y)

# Now move down and backward to actual grasp position
goto_pose_arm1(receive_pos, quat_arm1_down_y, z_approach=approach_distance)

# Finalize position without approach
goto_pose_arm1(receive_pos, quat_arm1_down_y)

# Close Arm1 gripper to grasp hammer handle
close_gripper_arm1()

# Now Arm0 can release
open_gripper_arm0()

# Optionally lift both arms slightly to finish
final_lift = receive_pos.copy()
final_lift[2] += 0.05

goto_pose_arm1(final_lift, quat_arm1_down_y)
goto_pose_arm0(handover_pos + [0, 0, 0.05], quat_arm0_down_x)