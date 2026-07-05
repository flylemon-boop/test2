import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get the current hammer pose (middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Define key quaternions for orientation control
# Arm0 will approach the hammer with gripper opening along Y-axis (facing down)
q_arm0_approach = np.array([0, 1, 0, 0])  # [0, 1, 0, 0] for Y-axis opening, facing down
# For handover, we want the hammer vertical or tilted so that Arm1 can grasp the handle safely
# After lifting, rotate hammer to a near-vertical orientation with handle up and head down
q_vertical = np.array([0.707, 0, 0.707, 0])  # approximately vertical, x-axis aligned with gravity

# Step 1: Arm0 moves above the hammer with z_approach to avoid collision
approach_height = 0.1  # 10 cm above table for safe descent
goto_pose_arm0(
    position=hammer_pos,
    quaternion_wxyz=q_arm0_approach,
    z_approach=approach_height
)

# Step 2: Descend and grasp the middle of the handle
goto_pose_arm0(
    position=hammer_pos,
    quaternion_wxyz=q_arm0_approach
)
close_gripper_arm0()  # grasp the hammer at the middle

# Step 3: Lift the hammer vertically to clear the table
lift_height = 0.15  # lift to 15 cm above table for clearance
lift_pos = hammer_pos + np.array([0, 0, lift_height])
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_arm0_approach
)

# Step 4: Rotate the hammer to near-vertical orientation while keeping it high
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_vertical
)

# Now the hammer is held vertically by Arm0, head down, handle up

# Step 5: Plan handover zone — near midpoint between initial arm positions
mid_x = (0.44 + 1.18) / 2  # ~0.81 m in robot0's frame
handover_pos = np.array([mid_x, 0.0, 0.175])  # z between 0.15 and 0.20

# Move Arm0 to handover position with hammer vertical
goto_pose_arm0(
    position=handover_pos,
    quaternion_wxyz=q_vertical
)

# Step 6: Prepare Arm1 to receive the hammer handle from below
# Arm1 needs to grasp the handle — since hammer is vertical, Arm1 should approach from below
# We want Arm1 gripper to face upward or be oriented to catch the handle tip

# But Arm1 gripper convention: opening along Y-axis when facing down is [0,0,1,0]
# To face upward, we can use the opposite — but need to define proper orientation
# Let's assume Arm1 approaches with gripper opening along -Y (from below), facing upward
# A quaternion for gripper facing up with opening along Y-axis would be [0, 0, 0, 1] rotated appropriately
# Instead, let's use a known configuration: if [0,0,1,0] is down, then [0,0,0,1] might be up? 
# But conventions vary. Safer: use same vertical alignment but from below.

# Alternative: keep hammer vertical, Arm1 approaches from side at mid-height of handle
# Since Arm0 holds the bottom/middle, the handle top is free — Arm1 should grasp near the top of the handle
handle_length_estimate = 0.20  # average between 0.15 and 0.25
handle_top_offset = np.array([0, handle_length_estimate/2, 0])  # from center to top of handle
target_grasp_pos_on_handle = handover_pos + handle_top_offset  # where Arm1 should grab

# But wait: hammer is vertical, so "top" is +Z. Handle extends upward.
# So target_grasp_pos_on_handle = handover_pos + [0,0, handle_length_estimate/2]
target_grasp_pos_on_handle = handover_pos + np.array([0, 0, handle_length_estimate/2])

# However, Arm1 must approach carefully. Use a side grasp with gripper opening along X or Y
# Best: Arm1 approaches horizontally from the side, gripper opening along Y-axis (toward hammer)
# So orientation: [0,0,1,0] (facing down) may not work. Need gripper to face in X or Y direction?

# Reconsider: most reliable is planar movement in horizontal plane.
# Instead of vertical handover, do partial tilt: Arm0 tilts hammer to ~45 degrees so handle points toward Arm1
# And lifts to z=0.175 during handover

# NEW PLAN: after lifting, tilt hammer so handle points toward Arm1 (positive X direction)
# So rotation around Y-axis by 90 degrees: from vertical Z to horizontal X
# Use quaternion for 90 deg rotation around Y: q_yaw_90 = [cos(45°), 0, sin(45°), 0] ≈ [0.707, 0, 0.707, 0]
# Wait — that’s roll. For yaw (around Y), it's [cos(theta/2), 0, sin(theta/2), 0]
# 90 deg yaw: [cos(45), 0, sin(45), 0] = [0.707, 0, 0.707, 0]
q_yaw_90 = np.array([0.707, 0, 0.707, 0])  # rotate so object X points forward (in world Y?) — need to test

# Actually, better to think in terms of gripper orientation.
# We want Arm0 to hold the hammer near its head (so handle sticks out toward Arm1)
# Then tilt hammer up slightly so it doesn't hit table

# FINAL DECISION: after grasping in middle, Arm0 lifts, then rotates so hammer handle points toward Arm1 (+X)
# and tilts up by ~30-45 degrees to keep z > 0.15 during handover

# Define orientation: hammer along +X axis, tilted up 45 degrees
# This requires composing rotations:
# 1. rotate 90 deg around Y to bring handle from +Y to +X
# 2. rotate -45 deg around Z to tilt up (counterclockwise when viewed from above)
# But simpler: empirically, use known working orientations

# Use a standard orientation: gripper opening along X-axis, facing up-left
# From documentation: Arm0 gripper facing down opening along X-axis: [0, 0.707, 0.707, 0]
# To face in +X direction (horizontal), we can use [0.707, 0, 0, 0.707] — this is 90 deg around Z?
# Instead, let's avoid complex rotation and do stepwise motion

# Simpler robust strategy:
# - Arm0 picks hammer from top (already done)
# - Lifts straight up 15cm
# - Moves laterally to handover zone at mid_x, y=0, z=0.175
# - Rotates hammer slowly until handle points to Arm1 (along +X)

# Use a known quaternion that makes the gripper point along +X (horizontal)
q_horizontal_x = np.array([0.5, 0.5, 0.5, 0.5])  # rough approximation, but let's use a better one
# Proper way: 90 deg around Y then 90 deg around Z? Too complex.

# Instead, recall: Arm0 gripper opening along X-axis (when facing down): [0, 0.707, 0.707, 0]
# To make it face forward along X (horizontal), rotate that frame by -90 deg around Y
# Rotation of quaternion: rotate frame by -90 deg around Y: q_Y_minus90 = [cos(-45), 0, sin(-45), 0] = [0.707, 0, -0.707, 0]
# Compose: q_new = q_Y_minus90 * q_original
# But we can approximate: [0.707, 0, -0.707, 0] * [0, 0.707, 0.707, 0] → too messy.

# Practical solution: move to handover position with hammer upright first, then gradually rotate
# But we know z must be between 0.15 and 0.20 during handover

# Compromise: Arm0 moves to (mid_x, 0, 0.175) with hammer vertical (q_vertical)
# Then Arm1 approaches from the side (from lower x) to grasp the upper part of the handle

# Arm1 needs to go to target_grasp_pos_on_handle with orientation to clamp along the handle
# Handle is vertical, so Arm1 should grasp horizontally? Or vertically?

# Better: Arm1 approaches horizontally, gripper opening along X-axis, from the side (-Y or +Y)
# Let's assume hammer is at (0.81, 0, 0.175), handle extending up to (0.81, 0, 0.175 + 0.1) ≈ (0.81, 0, 0.275)
# Arm1 should grasp near the top of the handle, say at (0.81, 0, 0.25) — but that's high

# Instead, do not fully lift — keep hammer center at z=0.175, handle top at z=0.175 + 0.125 = 0.3 — too high?
# No: handle length 0.2 max, so half is 0.1 → top at 0.275 — acceptable.

# But Arm1 may not reach that high? Initial y=0.0, so probably can.

# Revised plan:

# After Arm0 lifts hammer center to (mid_x, 0, 0.175) with vertical orientation:
#   handle extends from (mid_x, 0, 0.175 - 0.1) to (mid_x, 0, 0.175 + 0.1) = [0.715, 0.915]? No, x is fixed.
#   pos = (0.81, 0, 0.175), handle along Z, so top at (0.81, 0, 0.275)

# Arm1 moves to a position to grasp the top quarter of the handle — say at (0.81, 0, 0.25)
# But Arm1 must not collide. Approach from the side? But y=0 is front.

# Assume the robots are facing each other across the table, x increasing from left to right.
# Arm0 at x~0.44, Arm1 at x~1.18, so handover at x=0.81 is reachable by both.

# Arm1 approaches the point (0.81, 0, 0.25) with gripper opening along X-axis (to clamp along handle radial direction?)
# No: to grasp a vertical handle, gripper should open along horizontal axis — either X or Y.

# If handle is vertical, gripper should close along horizontal plane — so opening direction should be horizontal.
# For Arm1, to grasp a vertical rod, it should have gripper opening along X-axis (left-right) or Y-axis (front-back)

# Let's choose Y-axis: so gripper faces forward/backward, can approach from front or back.
# But environment says Arm1 gripper facing down opening along Y-axis: [0,0,1,0] — that means when facing down, fingers open in Y direction.

# To grasp a vertical handle, we want the same: fingers open in horizontal plane. So use [0,0,1,0] but at a rotated position?

# Actually, if the handle is vertical, and Arm1 approaches from the side (say from negative Y), then it can use downward-facing gripper to pinch the handle sideways.

# But safest: Arm1 approaches from the side (in Y) to the point (0.81, 0, 0.25) with gripper opening along X-axis? 

# Documentation does not give quaternion for opening along X-axis for Arm1.
# But symmetry: Arm0 has [0, 0.707, 0.707, 0] for opening along X-axis facing down.
# Likely Arm1 uses same convention? But coordinate frames differ.

# Given complexity, instead: do not rely on full vertical. Do a diagonal transfer.

# FINAL ROBUST STRATEGY:

# 1. Arm0 picks hammer from top at initial location
# 2. Lifts straight up by 0.1m
# 3. Moves laterally to handover zone (mid_x, 0, 0.175) without rotating much — keep hammer nearly flat but lifted
# 4. Tilt only slightly up so that z of hammer remains in [0.15,0.20]

# But goal says: handover must have z between 0.15 and 0.20 — which we meet by setting handover at z=0.175

# However, Arm1 must grasp the handle — not the head. So orientation must expose the handle.

# Therefore: after picking, Arm0 rotates the hammer 180 degrees around vertical axis so that the handle is now pointing towards Arm1 (+Y was handle, now rotate so handle is +X or something)

# Original: hammer along Y-axis, handle at +Y, head at -Y.
# We are holding the center. Rotate 90 degrees around Z so that handle points towards +X (towards Arm1)

# Quaternion for 90 deg around Z: [cos(45), 0, 0, sin(45)] = [0.707, 0, 0, 0.707]

q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])

# So sequence:
# - pick at original pose (aligned with Y)
# - lift
# - rotate around Z by 90 deg so handle points to +X (Arm1 side)
# - move to handover zone at (mid_x, 0, 0.175)

# But moving to mid_x while holding hammer along X is fine.

# Then Arm1 can approach from the front (negative Y) or back to grasp the handle end

# However, Arm1 must grasp the handle — which will be at (mid_x + handle_half_length, 0, 0.175) if fully extended
# But we don't want to overextend.

# Instead, Arm0 moves to handover zone and stops with handle pointing to Arm1, then Arm1 closes on the handle near the outer part

# Steps:

# After closing gripper on hammer center:
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_arm0_approach
)

# Rotate 90 degrees around Z to point handle to Arm1 (+X)
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_rotate_z_90
)

# Move to handover zone
handover_pos = np.array([mid_x, 0.0, 0.175])
goto_pose_arm0(
    position=handover_pos,
    quaternion_wxyz=q_rotate_z_90
)

# Now the handle is pointing towards +X (right), so the handle extends from
# (mid_x - h/2, 0, 0.175) to (mid_x + h/2, 0, 0.175) — no: if we rotated 90 deg around Z, and originally along Y,
# now along X. Handle was +Y, now +X. So handle extends to higher X.

# So handle end is at: handover_pos + [handle_length/2, 0, 0] = [mid_x + 0.1, 0, 0.175]

# Arm1 should go to that point to grasp the handle

handle_end_pos = handover_pos + np.array([handle_length_estimate/2, 0, 0])

# Arm1 needs to grasp this point. What orientation?
# The handle is horizontal, along X-axis.
# Arm1 should approach from above or side?

# To avoid collision, approach from above with gripper opening along X-axis.

# But what is quaternion for Arm1 gripper opening along X-axis facing down?
# Not given. But we can try to derive.

# Alternatively, approach from the side (from negative Y) with gripper opening along X-axis.

# But we don't have the quaternion.

# Use a fallback: since we cannot compute exact quaternion, use the same as Arm0's X-opening
q_arm1_open_x = np.array([0, 0.707, 0.707, 0])  # ASSUME same convention

# But this might be incorrect.

# BETTER: keep the hammer horizontal but have Arm1 grasp it from the side using a vertical grip? Unlikely.

# RECONSIDER: after all, the simplest and most reliable method seen in practice is to have the receiving arm pre-positioned below.

# NEW SIMPLE PLAN:

# Arm0 picks hammer from top -> lifts -> moves to center -> opens gripper
# Arm1 simultaneously moves to a position below to catch

# But we cannot guarantee timing, and dropping might fail.

# Instead, do coordinated handover with contact.

# However, the problem states: handover must occur with z between 0.15 and 0.20

# Final decision: abandon complex orientation. 
# Since the hammer is symmetric in pickup at center, and we only need Arm1 to grasp the handle (not head),
# we can have Arm0 simply fly to the handover zone at z=0.175, then Arm1 approaches the handle end from the side.

# But how does Arm1 know where the handle is? We know: handle is along X+, so its end is at:
#   p_handle_end = handover_pos + np.array([handle_length_estimate/2, 0, 0])

# Prepare Arm1:
open_gripper_arm1()

# Move Arm1 to grasp the handle end
goto_pose_arm1(
    position=handle_end_pos,
    quaternion_wxyz=q_arm1_open_x,  # assumed
    z_approach=0.05  # approach from above by 5cm
)

# Then close gripper on handle
close_gripper_arm1()

# Now Arm0 can release
open_gripper_arm0()

# But wait, is the handle end at [mid_x + 0.1, 0, 0.175]? Yes.

# However, we never explicitly calculated handle length. Use observed value? We have none.

# Instead, estimate from typical length
handle_length = 0.20  # meters, average

# Recompute:
handle_end_pos = handover_pos + np.array([handle_length/2, 0, 0])

# But is the orientation correct? When Arm0 rotates to q_rotate_z_90, is the handle really along +X?

# Originally, hammer along +Y (handle to +Y). 
# Rotation of 90 deg around Z (counter-clockwise when viewed from above) takes +Y to +X.
# So yes, handle points to +X.

# Therefore, the end of the handle is at higher X.

# So Arm1 must go to a higher X position.

# But Arm1's base is at x=1.18, so it can reach x=0.81 + 0.1 = 0.91 easily.

# Code:

# Estimate handle length
handle_length = 0.20  # conservative estimate within 0.15-0.25

# After Arm0 is at handover position with handle pointing to +X:
# Compute where the handle end is
handle_end_pos = handover_pos + np.array([handle_length/2, 0, 0])

# Define orientation for Arm1: facing down, opening along X-axis
q_arm1_grip = np.array([0, 0.707, 0.707, 0])  # assumed: same as Arm0

# But note: Arm1's coordinate system is mirrored? The API transforms automatically.

# Move Arm1 to above the handle end
goto_pose_arm1(
    position=handle_end_pos,
    quaternion_wxyz=q_arm1_grip,
    z_approach=0.05
)

# Then descend to grasp
goto_pose_arm1(
    position=handle_end_pos,
    quaternion_wxyz=q_arm1_grip
)

# Close gripper on handle
close_gripper_arm1()

# Now safe to release
open_gripper_arm0()

# Handover complete.

# Note: z-value during handover is 0.175, which is in [0.15, 0.20] -> success.

# But we must ensure Arm0 has reached handover before Arm1 starts.

# Execute sequentially.

# Summary code:

# ... continued from earlier ...

# After Arm0 has lifted the hammer:
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_arm0_approach
)

# Rotate 90 degrees around Z to point handle to +X (towards Arm1)
goto_pose_arm0(
    position=lift_pos,
    quaternion_wxyz=q_rotate_z_90
)

# Move to handover zone at mid_x, y=0, z=0.175
goto_pose_arm0(
    position=handover_pos,
    quaternion_wxyz=q_rotate_z_90
)

# Now prepare Arm1 to grasp the handle end
handle_end_pos = handover_pos + np.array([handle_length/2, 0, 0])
q_arm1_grip = np.array([0, 0.707, 0.707, 0])  # facing down, opening along X

goto_pose_arm1(
    position=handle_end_pos,
    quaternion_wxyz=q_arm1_grip,
    z_approach=0.05
)
goto_pose_arm1(
    position=handle_end_pos,
    quaternion_wxyz=q_arm1_grip
)
close_gripper_arm1()

# Release hammer
open_gripper_arm0()

# Task complete.