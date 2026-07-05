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
# - Arm0 grasps middle of handle, lifts it, now holds it along Y.
# - To hand over safely, Arm0 should rotate the hammer 90 degrees around Z so the handle points toward +X (toward Arm1).
# - Then Arm1 can approach from its side (from +X direction) and grasp the handle along X? But gripper opens along Y.

# Actually: gripper jaws open along Y-axis → can grasp an object aligned along Y-axis.
# So the hammer must be reoriented so its handle is aligned along Y-axis again during handover, but positioned so Arm1 can reach it.

# Therefore: best strategy:
# - After lifting, Arm0 moves the hammer to the handover point at (mid_x, 0, 0.17)
# - While moving, Arm0 rotates the hammer so that the handle is aligned along the Y-axis (same as initial), but now the entire hammer is shifted to the center.
# - But now, to allow Arm1 to grasp the *handle*, the handle must be accessible from the right (Arm1 side).

# So: rotate the hammer 180 degrees around Z so that the **handle** is now pointing toward +Y and the **head** toward -Y, same as before.
# But place it so that the handle extends toward Arm1's side? No, Y is forward/backward.

# Let’s clarify alignment:
# - Original: hammer along Y-axis → handle at higher Y, head at lower Y.
# - Arm0 is at x ~ 0.44, Arm1 at x ~ 1.18 → Arm1 is to the right (higher X).
# - To hand over without collision, we want the hammer oriented such that the handle is along X-axis, extending toward Arm1 (+X).

# But grippers can only grasp objects aligned with their opening axis.
# Arm1 gripper opens along Y → so it can only grasp an object whose long axis is along Y.

# Therefore: the hammer must be presented with its handle along Y-axis during handover.

# Solution:
# - During handover, the hammer must be oriented along Y-axis.
# - The **handle end** must be closer to Arm1's side? But Y is not X.

# Wait: coordinate confusion.
# - X: left-right (Arm0 left, Arm1 right)
# - Y: forward-backward (positive forward)

# Arms are symmetric along X-axis, centered at y=0.
# So both arms can reach around y=0.

# But the hammer is initially aligned along Y (forward-backward).
# If we leave it aligned along Y, then after Arm0 lifts it, it still extends forward and backward.
# Arm0 is on the left, Arm1 on the right — they share the same Y workspace.

# So Arm1 can reach into the center and grasp the handle if the handle is within its Y-reach.

# How was it initially placed? Handle toward +Y (forward), head toward -Y (backward).
# When Arm0 picks up the middle of the handle, the front half of the handle (+Y side) is still forward.

# For Arm1 to grasp the handle, it needs to grasp the part of the handle that was originally behind the grasp point (i.e., closer to the head).
# But that would require Arm1 to reach over or under.

# Better: after picking up, Arm0 rotates the hammer 180 degrees around Z so that the **handle now points backward (-Y)** and head forward (+Y).
# Then, when at handover position, Arm1 can approach from the front (+Y direction) and grasp the handle.

# However, rotation may cause collisions.

# Alternative idea:
# - Don’t rotate the hammer.
# - Arm0 brings the hammer (still oriented along +Y) to the handover zone at (mid_x, 0, 0.17)
# - The handle extends from the grasp point forward (+Y), length/2 forward and back.
# - Arm1 approaches from the right (+X direction) and grasps the handle part that is on the right side? But the handle is thin.

# But the problem says: "Arm 1 should then grasp the hammer handle (not hammer head)"
# And "The z-value of hammer must be between 0.15 and 0.20 during the handover"

# Given constraints, safest is:
# - Arm0 lifts the hammer without rotating (maintains Y-alignment)
# - Moves to (mid_x, 0, 0.17) — this is above the central area, but we assume there's enough table or clearance
# - At this point, the handle extends from approximately (mid_x, hammer_pos[1]+L/2, 0.17) to (mid_x, hammer_pos[1]-L/2, 0.17)
#   where L is handle length (0.15–0.25m), so ±(0.075 to 0.125) in Y

# But hammer was initially at some y0 — we don't know exactly, but roughly aligned at y~0?

# Assume the initial hammer position (middle of handle) is near (0.81, 0, z_table) since Arm0 is at (0.44,0) and Arm1 at (1.18,0), midpoint ~0.81

# So handover at (0.81, 0, 0.17) is safe.

# Now, Arm1 needs to grasp the handle — which is currently held by Arm0 at its center.
# So the half of the handle that is toward +Y is free.

# But Arm1 is at x=1.18, so it can reach leftward to x=0.81.

# Arm1 should approach the handle from below or above? But z is fixed at 0.17.

# Best: Arm1 approaches from the +X direction (right to left) along X-axis, but to grasp an object aligned along Y, it needs to align its gripper.

# Arm1's gripper opens along Y → so it can grasp an object along Y-axis by approaching along X.

# Yes! So if the hammer is aligned along Y, Arm1 can approach along X and close its gripper to grab the handle.

# But where on the handle? It must grasp a part of the handle, not the head.

# Current state: Arm0 is holding the center of the handle.
# The handle extends from center -L/2 to center +L/2 along Y.
# The head is attached at center -L/2 - (some offset)? Actually, the function returns middle of handle.

# So entire handle is from `hammer_pos - [0, L/2, 0]` to `hammer_pos + [0, L/2, 0]`, with head beyond -L/2.

# So any point on the handle has Y between hammer_pos[1] - L/2 and hammer_pos[1] + L/2.

# But after lifting, the whole thing is moved.

# To enable Arm1 to grasp the handle, Arm0 should move so that the portion of the handle near Arm1 is available.

# But Arm0 is holding the center — so both sides are symmetric.

# So Arm1 can grasp either side — but must avoid the head.

# The head is at the -Y end of the handle.

# So as long as Arm1 grasps at a point where Y > hammer_pos[1], it should be on the handle (assuming symmetry).

# But we moved it — so the new position of the handle middle is at handover_pos = (mid_x, 0, 0.17)

# So handle extends from (mid_x, -L/2, 0.17) to (mid_x, L/2, 0.17), head at (mid_x, -L/2 - something, ...) — so definitely, Y >= -L/2 is handle.

# L_min = 0.15 → -L/2 = -0.075

# So if Arm1 grasps at Y > -0.075, it might be on handle? But need to be careful.

# But actually, the entire segment [-L/2, L/2] relative to center is handle.

# So Arm1 should grasp at a point on the handle that is within this range.

# Since Arm0 is holding the center, the handle extends forward (+Y) and backward (-Y) equally.

# The head is attached to the -Y end.

# So Arm1 should grasp the handle at a point that is not too close to the -Y end.

# Ideal: grasp near the +Y end (farthest from head).

# But Arm1 is coming from +X, so it can choose where to grip along Y.

# We can have Arm1 attempt to grasp at (mid_x, 0.1, 0.17) — but wait, that’s occupied by the hammer body.

# Instead, we need to define a grasp pose for Arm1 on the hammer handle.

# But we cannot directly command that — we must use goto_pose_arm1 to a specific position.

# Idea:
# - After Arm0 reaches handover position, it keeps holding.
# - Arm1 moves to a pose above the handle at the +Y end, then descends to grasp.

# But the handle is only up to L/2 ≈ 0.125m in +Y from center.

# So let's set Arm1's grasp target at:
#   grasp_offset_y = 0.1  # 10 cm along +Y from center of handle (which is at handover_pos)
#   So target position = handover_pos + [0, 0.1, 0] = [mid_x, 0.1, 0.17]
# But that’s not correct — the handle is rigid, we can't grasp arbitrarily.

# We need Arm1 to grasp the handle while it's being held by Arm0.

# But both arms cannot hold the same object safely without coordination.

# The task is "hand it over" — so Arm0 must release after Arm1 grasps.

# Sequence:
# 1. Arm0 lifts and moves to handover position (mid_x, 0, 0.17), orientation unchanged (along Y)
# 2. Arm1 moves to a pose above the intended grasp point on the handle
#    Intended grasp point: somewhere on the handle away from the head, say at (mid_x, 0.05, 0.17)
#    But to avoid collision, approach from above with z_approach
# 3. Arm1 descends and closes gripper
# 4. Arm0 opens gripper
# 5. Arm1 lifts slightly to take full weight

# But is the handle long enough that y=0.05 is still on the handle? Yes, since min half-length is 0.075m.

# So grasp at y = +0.075 would be the tip — but safer to grasp at y = +0.05.

# So define:
handover_position = np.array([mid_x, 0.0, handover_z])  # where Arm0 brings the center of the handle

# Point on handle for Arm1 to grasp: 5 cm toward +Y from center
grasp_point_arm1 = handover_position + np.array([0, 0.05, 0])

# But Arm1 must approach vertically from above
approach_point_arm1 = grasp_point_arm1 + np.array([0, 0, z_offset])

# Orientation: Arm1 gripper opening along Y-axis → [0,0,1,0]
q_arm1_approach = q_arm1_grasp  # [0,0,1,0]

# Move Arm0 to handover position
goto_pose_arm0(handover_position, q_arm0_approach)

# Now Arm1 moves to above the grasp point
goto_pose_arm1(approach_point_arm1, q_arm1_approach, z_approach=0.0)

# Descend to grasp point
goto_pose_arm1(grasp_point_arm1, q_arm1_approach, z_approach=-z_offset)

# Close Arm1 gripper to grasp the handle
close_gripper_arm1()

# Now, Arm0 can release
open_gripper_arm0()

# Finally, Arm1 lifts the hammer slightly to complete the handover
lifted_by_arm1 = grasp_point_arm1 + np.array([0, 0, 0.05])
goto_pose_arm1(lifted_by_arm1, q_arm1_approach)

# Task complete