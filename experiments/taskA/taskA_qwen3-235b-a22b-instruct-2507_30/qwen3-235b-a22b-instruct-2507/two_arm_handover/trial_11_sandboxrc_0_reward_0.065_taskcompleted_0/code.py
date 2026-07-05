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
handover_z = 0.17  # Within required 0.15-0.20 range

# Target handover position (Arm0 will bring hammer here)
handover_pos = np.array([handover_x, handover_y, handover_z])

# But we must rotate the hammer so that Arm1 can grasp the handle properly.
# Currently, hammer lies along Y-axis (handle +Y, head -Y). 
# After Arm0 picks it up from the middle, to hand over to Arm1:
# We want the handle to be oriented toward Arm1's side (+X direction), so we rotate the hammer 90 degrees.

# So when handing over, the hammer should be rotated so its handle points toward +X
# This means the gripper of Arm0 must rotate accordingly during handover.
# Desired orientation: hammer aligned along X-axis, handle toward +X → gripper opening should be along Z or Y?
# But grippers open along local Y or X depending on setup.

# Since Arm1 uses [0,0,1,0] for Y-axis opening (gripper jaws move along Y), to grasp the handle,
# the handle must be aligned along Y-axis again? But wait: if hammer is handed over with handle along X,
# then Arm1 cannot grasp unless it approaches along X.

# Reconsider: 
# - Initial: hammer along Y (handle +Y, head -Y)
# - Arm0 grasps middle — so now it holds center, can reorient.
# - To hand over safely, we want Arm1 to grasp the *handle* (not head). So Arm1 must approach from the head side (-Y relative to handle).
# But due to physical layout (Arms on left/right), best way is to rotate hammer 90 degrees so handle points to right (+X).

# So final orientation: hammer along X-axis, handle toward +X (toward Arm1), head toward -X (toward Arm0)
# Then Arm1 can approach along Y-axis to grasp the handle (since its gripper opens along Y locally).

# Therefore, during handover, the hammer should be oriented with handle along +X.
# So the gripper holding it (Arm0) must have its opening direction compatible.

# How to orient Arm0's gripper to hold hammer along X-axis?
# Initially, it approached along Y (gripper opening along Y) to grab handle along Y.
# Now we need to rotate the object so it lies along X.
# We can rotate the wrist: rotating by 90 degrees around Z-axis changes Y-aligned to X-aligned.

# Rotation quaternion for 90 deg CCW around Z: [cos(45), 0, 0, sin(45)] -> [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])  # 90 deg CCW around Z

# Apply rotation to original approach quat
q_handover_orientation = q_rotate_z_90  # We'll manually set desired orientation
# Actually, composing rotations: we want to rotate the tool frame by 90 deg around Z
# The correct resulting quaternion when applying 90 deg Z-rotation to [0,1,0,0] is approximately [0.707, 0, 0, 0.707]? 
# Let’s compute: rotating vector (0,1,0) by 90 deg CCW around Z gives (-1,0,0) — not what we want.

# Wait: we want the *opening direction* (the direction the jaws move) to allow gripping along X-axis.
# Original: q=[0,1,0,0] => opening along +Y and -Y
# After 90 deg CW around Z (to make opening along +X/-X): that would be quaternion [0.707, 0, 0, -0.707]

# But actually, for the hammer to lie along X-axis with handle toward +X, the gripper must be squeezing along X,
# meaning the opening direction is X — so we want the gripper to open along X.

# From documentation:
# - Arm0 gripper facing down opening along X-axis: [0, 0.707, 0.707, 0]
# So we can use that directly.

q_arm0_handle_x = np.array([0, 0.707, 0.707, 0])  # opening along X-axis

# So after lifting, Arm0 will reorient the hammer from Y-along to X-along

# First, move to handover position with intermediate orientation for safety
intermediate_lift_pos = lifted_pos_arm0.copy()
intermediate_lift_pos[2] = max(intermediate_lift_pos[2], 0.2)  # Lift slightly higher before moving

# Move laterally to above handover zone with safe height and orientation
goto_pose_arm0(handover_pos + np.array([0,0,0.05]), q_arm0_handle_x)

# Then descend carefully to handover_z
goto_pose_arm0(handover_pos, q_arm0_handle_x)

# At this point, hammer is at handover position, oriented with handle toward +X, z in valid range

# Step 4: Arm1 moves to grasp the handle
# Handle center is now at handover_pos, but Arm1 needs to grasp the *handle*, so offset?
# Since hammer handle length is between 0.15 and 0.25m, and currently centered at handover_pos,
# and oriented along +X, then the handle extends from handover_pos to handover_pos + (0.15 to 0.25, 0, 0)
# But we want Arm1 to grasp the handle — ideally not too far out.

# However, the API only allows us to go to poses — we don't know exact handle length.
# Best guess: assume half-length ~0.2m, so grasp at center + (0.1, 0, 0)? But wait — no.
# Currently, Arm0 is holding the *center* of the hammer.
# The *handle* is the part from center to +X direction (length ~0.15–0.25m).
# We want Arm1 to grasp somewhere on the handle — say, 0.15m from center toward +X.

handle_grasp_offset = 0.15  # meters along +X
arm1_grasp_pos = handover_pos + np.array([handle_grasp_offset, 0, 0])

# But wait: the entire hammer is being moved — if Arm1 moves to that point now, collision may occur.
# Instead, the handover happens at handover_pos — but Arm1 should grasp while Arm0 releases.

# Correction: Arm0 brings the hammer to handover location with handle pointing to Arm1 (+X).
# Then Arm1 approaches along Y-axis to grasp the handle at the center (currently held by Arm0)? That doesn't work.

# Rethink: both arms need to coordinate around the same point.
# Better plan:
# - Arm0 brings the hammer so that the **handle end** is near the handover zone.
# But we don't know handle length exactly.

# Alternative idea:
# Keep Arm0 holding the center, bring it to x = mid_x - some_offset, so that the handle extends toward Arm1.
# But we lack precise knowledge.

# Simpler and safer: 
# Perform handover at the center of the hammer, but with the hammer rotated so that the **handle is accessible** to Arm1.
# Since the hammer is symmetric across its long axis, Arm1 can grasp the handle portion while Arm0 holds the center.

# But physically, both grippers cannot occupy same space.

# Correct strategy:
# Rotate hammer 180 degrees around Z so that the *handle* is on the +X side and *head* on -X.
# Then Arm0 holds center, which is now at position where the *head* is behind it (-X) and handle sticks out toward Arm1 (+X).
# Then Arm1 can grasp the handle section without Arm0 being in the way.

# We already planned that: our handover_pos has hammer along X, handle toward +X, head toward -X, Arm0 at center.

# Now Arm1 must approach from the front/back (Y direction) to grasp the handle.
# But where on the handle? Ideally, near the end, but we risk dropping.

# Since we don't know exact length, safest is to have Arm1 grasp the handle as close as possible to the center, but Arm0 must release first?

# No — coordinated handover: both grasp simultaneously, then Arm0 releases.

# But to avoid collision, Arm1 should approach perpendicular to hammer axis.

# Plan:
# Arm1 approaches along Y-axis to the point on the handle that is offset from center by +dx in X.
# But again, we don't know dx.

# Compromise:
# Assume average handle length = 0.2m, so we let Arm1 try to grasp at 0.15m from center along +X.
# But we must also account for Arm1's gripper width and reach.

# However, due to uncertainty, better to have Arm1 grasp at the same point (center) after Arm0 rotates appropriately? Not possible.

# Revised realistic plan:
# During handover, both arms grasp the hammer near the center, but on opposite sides.
# But they might collide.

# Use conservative safe transfer:
# 1. Arm0 lifts hammer and moves to handover location, oriented with handle along +X.
# 2. Arm0 raises slightly and opens gripper, letting hammer rest momentarily on table? Not allowed — table may not span center.
# 3. Risky.

# Instead, we do a "buddy pass":
# - Arm1 moves to a pose just beside the handle (offset in Y) with gripper open, ready to close.
# - Then Arm0 moves into position, and Arm1 closes, then Arm0 opens.

# But how to coordinate spatially?

# Best bet:
# - Handover occurs with hammer horizontal, z=0.17m, at (mid_x, 0, 0.17)
# - Hammer oriented along X, handle toward +X
# - Arm0 holds the center
# - Arm1 approaches from +Y side, along Y-axis, to grasp the handle at a point 0.1m from center toward +X

grasp_point_on_handle = handover_pos + np.array([0.1, 0, 0])  # estimate

# But Arm1 must approach along Y, so we define approach path

# First, Arm1 moves above the grasp point with z_approach
approach_offset_z = 0.05
arm1_approach_pos = grasp_point_on_handle + np.array([0, 0, approach_offset_z])

# Arm1 should approach with gripper opening along Y-axis (so it can grasp along Y)
# Reference: Arm1 gripper facing down opening along Y-axis: [0, 0, 1, 0]
# So it approaches vertically

goto_pose_arm1(arm1_approach_pos, q_arm1_grasp, z_approach=0.0)

# Then descend to grasp
goto_pose_arm1(grasp_point_on_handle, q_arm1_grasp, z_approach=-approach_offset_z)

# Close gripper to secure handle
close_gripper_arm1()

# Now Arm0 can open gripper
open_gripper_arm0()

# Optional: Arm0 retracts slightly to avoid interference
retract_dist = 0.05
retract_dir = np.array([-1, 0, 0])  # move back in X
retract_pos = handover_pos + retract_dir * retract_dist
goto_pose_arm0(retract_pos, q_arm0_handle_x)

# Task complete