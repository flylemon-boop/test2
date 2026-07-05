import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

# Lift both arms up by 0.1 meters in Z to clear any potential obstruction
lift_offset = np.array([0, 0, 0.1])
goto_pose_both(pos0 + lift_offset, quat0, pos1 + lift_offset, quat1)

# Get the current positions of handle 0 and handle 1
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define desired gripper orientation: sideways grasp with gripper y-axis aligned to world z-axis
# This means the gripper will approach from the side, not top-down.
# Target rotation: We want the gripper's y-axis (which is forward when closing) to point upward (world z)
# A suitable quaternion for this is a 90-degree rotation around the x-axis from default [0,0,1,0] top-down
# Rotating 90 degrees around x-axis: gives quaternion [cos(45°), sin(45°), 0, 0] ≈ [0.707, 0.707, 0, 0]
# But we need to ensure that the gripper fingers are vertical and grasp horizontally
# Let's use a quaternion that orients the gripper so that it faces along the X-axis (for arm0 on left) 
# and -X-axis (for arm1 on right), with Y pointing up.

# For arm0 (left side): want gripper to face toward center (positive x-direction), Y up => use rotation: R_x(-90) * R_z(-90)
# Final quaternion for arm0: approximately [0.5, 0.5, -0.5, 0.5] (needs normalization) -> actually better to construct properly

# Instead, we define a standard sideways grasp where:
#   gripper_forward_axis = world_x (for arm0 approaching from -x side)
#   gripper_up_axis = world_z
# Use a fixed known good sideways grasp: rotate base [0,0,1,0] by -90 degrees around x-axis -> [0.707, -0.707, 0, 0]

sideways_quat = np.array([0.707, -0.707, 0, 0])  # From top-down to front-facing, y up

# However, for correct alignment, let’s adjust based on expected setup:
# Assume arm0 is on the -y side, arm1 on the +y side? Or opposite x?
# Since pot is centered and handles are on opposite sides, assume:
#   handle0 is on the left (arm0 side) at some (x, y-, z), handle1 on right (arm1 side) at (x, y+, z)
# So arm0 should approach from negative y direction -> gripper should face in positive y
# arm1 should approach from positive y direction -> gripper should face in negative y
# To have gripper face in +Y (arm0): rotate identity (facing x) by -90 deg around z -> quat_z(-90) = [0.707, 0, 0, -0.707]
# Then tilt down by 90 deg around x -> total quat = compose(quat_x(-90), quat_z(-90))

# Simpler: use a known working sideways grasp for horizontal grasp with fingers vertical
# After testing, common solution is to rotate [0,0,1,0] by 90 deg around x then adjust
# Final safe sideways grasp with fingers vertical and palm facing inward:
#   Use quaternion: w=0.5, x=0.5, y=0.5, z=0.5 (after proper construction)

# Actually, use a standard one: rotating from default [0,0,1,0] (top-down) by -90 deg about x-axis gives [0.707, -0.707, 0, 0]
# But this makes gripper face forward (along y). We want it to face radially toward the center.

# Let's re-define based on direction:

# For arm0: approaching handle0 from the side, we want:
#   approach direction: from current position toward handle0
# But since we know relative layout, assume:
#   handle0 is at center_y - offset, so arm0 comes from below in y
#   thus, arm0 should face in +y direction

# We build quaternion that points gripper forward (+Y) with up = +Z
# Forward vector = [0, 1, 0], Up vector = [0, 0, 1]
# Can use look-at style construction

def vec_to_quat(forward, up):
    # Orthonormal basis
    f = forward / np.linalg.norm(forward)
    u = up / np.linalg.norm(up)
    r = np.cross(f, u)  # right vector
    u = np.cross(r, f)  # recompute up
    # Rotation matrix
    R = np.array([r, f, u])
    # Convert to quaternion
    tr = np.trace(R)
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2
        w = 0.25 * S
        x = (R[2,1] - R[1,2]) / S
        y = (R[0,2] - R[2,0]) / S
        z = (R[1,0] - R[0,1]) / S
    else:
        if R[0,0] > R[1,1] and R[0,0] > R[2,2]:
            S = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
            w = (R[2,1] - R[1,2]) / S
            x = 0.25 * S
            y = (R[0,1] + R[1,0]) / S
            z = (R[0,2] + R[2,0]) / S
        elif R[1,1] > R[2,2]:
            S = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
            w = (R[0,2] - R[2,0]) / S
            x = (R[0,1] + R[1,0]) / S
            y = 0.25 * S
            z = (R[1,2] + R[2,1]) / S
        else:
            S = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
            w = (R[1,0] - R[0,1]) / S
            x = (R[0,2] + R[2,0]) / S
            y = (R[1,2] + R[2,1]) / S
            z = 0.25 * S
    quat = np.array([w, x, y, z])
    return quat / np.linalg.norm(quat)

# For arm0: wants to face toward handle0, but we already know handle0 position
# Actually, gripper should face along the direction from arm0's approach side to handle0
# But since arm0 is likely on the -y side, direction to handle0 is +y
# However, after lifting, we just go directly.

# Instead, use a fixed sideways orientation with fingers vertical and gripper facing inward
# Use a known good quaternion for sideways grasp: [0.924, -0.383, 0, 0] (approximate 45deg tilt?) — no.

# After standard practices: use quaternion that rotates from canonical [0,0,1,0] by -90 deg around x-axis
# This gives: cos(-45)=0.707, sin(-45)=-0.707 -> [0.707, -0.707, 0, 0]
# But this makes gripper face along y-axis.

# Let's define the grasp quaternions as sideways with y up and fingers opening along x
# Actually, Franka gripper: when quaternion is [0,0,1,0], it's top-down, fingers open along x/y
# We want fingers open along x/z? No, we want to grasp the handle from the side, so the fingers should close vertically
# So the gripper should be rotated so that its y-axis (forward) is along the horizontal radial direction
# and its z-axis (up) is aligned with world z

# Therefore, we can use:
#   For arm0: approaching from the -y side, so forward = +y, up = +z
#   For arm1: approaching from the +y side, so forward = -y, up = +z

# Compute quaternions
forward0 = np.array([0, 1, 0])  # arm0 faces +y
up0 = np.array([0, 0, 1])
quat0_desired = vec_to_quat(forward0, up0)

forward1 = np.array([0, -1, 0])  # arm1 faces -y
up1 = np.array([0, 0, 1])
quat1_desired = vec_to_quat(forward1, up1)

# Grasp height: directly at handle position
# But first, approach from a small z offset to avoid collision
approach_distance = 0.05  # 5 cm above the handle

# Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach poses (above the handles)
approach_pos0 = handle0_pos + np.array([0, 0, approach_distance])
approach_pos1 = handle1_pos + np.array([0, 0, approach_distance])

goto_pose_both(approach_pos0, quat0_desired, approach_pos1, quat1_desired)

# Now lower to grasp the handles without z_approach because we are controlling the path
# Use z_approach=0.0 since we are already above
goto_pose_both(handle0_pos, quat0_desired, handle1_pos, quat1_desired, z_approach=0.0)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift both arms simultaneously to the same target height
lift_height = 0.1  # lift 10 cm up from current handle position
target_lift_pos0 = handle0_pos + np.array([0, 0, lift_height])
target_lift_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(target_lift_pos0, quat0_desired, target_lift_pos1, quat1_desired)

# Task complete