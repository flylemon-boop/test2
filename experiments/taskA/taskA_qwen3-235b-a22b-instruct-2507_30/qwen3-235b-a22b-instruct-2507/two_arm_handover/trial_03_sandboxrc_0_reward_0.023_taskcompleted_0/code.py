# Code block 0
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
lift_height = 0.2  # High enough to avoid table and allow transfer
lifted_hammer_pos = hammer_pos.copy()
lifted_hammer_pos[2] = lift_height
goto_pose_arm0(lifted_hammer_pos, q_arm0_grasp)

# Step 3: Move hammer toward midpoint between arms for handover
# Estimate midpoint in x-direction between initial arm positions
mid_x = (0.44 + 1.18) / 2.0
midpoint = np.array([mid_x, 0.0, lift_height])

# We need to reorient the hammer so that Arm1 can grasp the handle
# The handle is currently aligned with Y-axis, with handle toward +Y
# Arm1 will grasp along the handle (along Y), so gripper should open along Y-axis

# But first, move Arm0 to midpoint at safe height
goto_pose_arm0(midpoint, q_arm0_grasp)

# Now adjust hammer z to be within required range [0.15, 0.20] for handover
handover_z = 0.17  # Midway in valid range
midpoint_handover = midpoint.copy()
midpoint_handover[2] = handover_z

# Reposition at correct handover height
goto_pose_arm0(midpoint_handover, q_arm0_grasp)

# Prepare desired orientation: rotate hammer 90 degrees around Z so handle points toward Arm1 (X direction)
# Current setup: handle along Y-axis (+Y is tip of handle). We want to rotate so that handle points toward +X (toward Arm1)
# This requires a 90-degree rotation about Z-axis from Y to X.
# A 90-degree rotation around Z-axis uses quaternion [cos(45°), 0, 0, sin(45°)] → [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])

# Apply rotation to current gripper orientation (q_arm0_grasp) to get new orientation
# Since we're rotating the entire tool frame, we compose quaternions: q_new = q_rotate * q_original
def quat_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return np.array([w, x, y, z])

# Rotate the gripper orientation so that after rotation, the gripper opens along X but now the handle points toward +X
# Actually, we want to rotate the *hammer*, not necessarily the gripper frame. 
# Instead, we should set a final orientation where the gripper still faces down, but rotated 90 deg in Z.

# Final orientation: down-facing, but rotated 90 deg about Z → this makes opening direction go from X to Y? 
# Let's reconsider: 
# Original Arm0 gripper opening along X → after +90 deg Z rotation, opening would be along Y.
# But we don't want that. We want to keep control.

# Actually, best strategy:
# Keep Arm0's gripper orientation fixed (facing down, opening along X) and just translate.
# Instead, we will pass the hammer by moving it to midpoint and having Arm1 come from the side.

# But Arm1 needs to grasp the handle, which is currently oriented along Y.
# After lifting, we can rotate the hammer 90 degrees so the handle lies along X-axis (from Arm0 to Arm1).
# So the handle extends from (mid_x - L/2, 0, z) to (mid_x + L/2, 0, z), with head near Arm0, tip near Arm1.

# To do this, we rotate the hammer around its center by 90 deg about Z-axis.
# However, when we rotate, the center stays fixed, but Arm0 is holding one end.

# Instead: incremental rotation while maintaining grip.

# Safer plan:
# 1. Move hammer to midpoint at handover height
# 2. Rotate slowly in place by 90 deg so handle aligns with X-axis
# 3. Arm1 approaches from +X side to grasp the handle near the tip

# Compute rotated orientation for hammer: after 90 deg CCW Z rotation, the handle will point +X
# The gripper must now face down but with opening direction along Y-axis? 
# But our gripper is holding the middle — so as long as it maintains grip on the center, orientation may not matter.

# However, Franka gripper has fingers along X or Y depending on orientation.
# Initially, Arm0 gripper was opening along X — so fingers were perpendicular to handle (which was along Y). That worked.
# After rotating handle to lie along X, we still need fingers perpendicular — so now fingers should be along Y.

# Therefore, we must change gripper orientation to opening along Y: [0, 1, 0, 0]

q_arm0_rotated = np.array([0, 1, 0, 0])  # Opening along Y-axis

# Perform partial rotation in steps to avoid large IK jumps or collisions
num_steps = 5
for i in range(1, num_steps + 1):
    t = i / num_steps
    # Interpolate orientation: slerp-like (simple lerp for small steps)
    q_step = quat_multiply(
        q_rotate_z_90,  # full 90 deg rot
        np.array([np.cos(np.pi/2 * t / 2), 0, 0, np.sin(np.pi/2 * t / 2)])  # fractional rotation
    )
    # Start from original grasp orientation and apply incremental rotation
    # Actually simpler: interpolate between q_arm0_grasp and q_arm0_rotated?
    # But that’s not a pure Z rotation.

    # Instead, create intermediate quaternions for 90 deg Z rotation applied gradually
    angle = np.pi/2 * t
    q_interp = np.array([np.cos(angle/2), 0, 0, np.sin(angle/2)])
    # Apply to original orientation
    q_current = quat_multiply(q_interp, np.array([0, 0.707, 0.707, 0]))
    q_current /= np.linalg.norm(q_current)
    
    goto_pose_arm0(midpoint_handover, q_current)

# Final orientation: fully rotated
goto_pose_arm0(midpoint_handover, q_arm0_rotated)

# Step 4: Arm1 moves to grasp the hammer handle
# The hammer handle is now aligned along X-axis, centered at midpoint_handover
# Handle length is between 0.15 and 0.25 — assume worst case 0.25
# So tip of handle is at: midpoint_handover[0] + 0.125, same y, z
handle_tip_x = midpoint_handover[0] + 0.125
grasp_point_arm1 = np.array([handle_tip_x, 0.0, handover_z])

# But Arm1 needs to approach from the side? No — since gripper opens along Y-axis, it will squeeze along Y.
# But the handle is along X, so Arm1 should approach along Y (from front or back).

# Since environment says Arm1 gripper opening along Y-axis: [0,0,1,0] → opening direction is Y
# So fingers move along Y-axis, so to grasp a bar along X, it must approach along Y.

# Yes — so Arm1 should approach along Y-axis to grasp the handle at its tip.

# Pre-grasp position: approach from +Y direction (front) with offset
approach_dist = 0.1
pre_grasp_arm1 = grasp_point_arm1 + np.array([0, approach_dist, 0])

# Move Arm1 above pre-grasp to avoid collision
goto_pose_arm1(pre_grasp_arm1 + np.array([0, 0, 0.1]), q_arm1_grasp)

# Then descend to pre-grasp
goto_pose_arm1(pre_grasp_arm1, q_arm1_grasp, z_approach=safe_z_above_table)

# Now move forward along Y to insert into grasp position
final_grasp_arm1 = grasp_point_arm1.copy()
final_grasp_arm1[1] -= approach_dist  # move back by approach_dist to reach actual point

# But we must maintain z_constraint: final z must be between 0.15 and 0.20
# We are already at handover_z = 0.17

goto_pose_arm1(final_grasp_arm1, q_arm1_grasp)

# Close Arm1's gripper to grasp the handle
close_gripper_arm1()

# Step 5: Arm0 releases and retreats
open_gripper_arm0()

# Arm0 retreats vertically first to avoid collision
retreat_pos = midpoint_handover + np.array([0, 0, 0.1])
goto_pose_arm0(retreat_pos, q_arm0_rotated)

# Task complete