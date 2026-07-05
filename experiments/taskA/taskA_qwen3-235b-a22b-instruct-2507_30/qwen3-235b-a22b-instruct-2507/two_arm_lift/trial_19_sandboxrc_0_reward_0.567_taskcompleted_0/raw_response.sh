import numpy as np

# First, slightly lift both arms to avoid occlusion
lift_height = 0.1
pos0_init, quat0_init = get_arm0_gripper_pose()
pos1_init, quat1_init = get_arm1_gripper_pose()

# Lift both arms up by lift_height in z-axis
pos0_lifted = pos0_init + np.array([0, 0, lift_height])
pos1_lifted = pos1_init + np.array([0, 0, lift_height])

goto_pose_both(pos0_lifted, quat0_init, pos1_lifted, quat1_init)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Desired grasp orientation: sideways grasp with gripper y-axis aligned with world z-axis.
# This means the gripper should approach horizontally.
# For Franka Emika, a suitable quaternion for horizontal grasp from side is typically:
# pointing in +x direction with y up -> corresponds to rotation of -90 degrees around z then -90 around y
# But we want the gripper's y-axis aligned with world z-axis -> so the gripper is "on its side"
# A good candidate: rotation that aligns gripper forward (usually -z) to point toward handle, and gripper y to world z.

# We'll define quaternions based on desired rotation.
# Let’s assume standard robot frame: x forward, y left, z up.
# For arm0 (on one side), it should approach along the y-axis (toward center), so direction = normalized vector from arm0 side to handle0.
# But since the pot is centered and handles are on opposite sides, arm0 likely approaches in +y direction, arm1 in -y.

# Compute approach directions
approach_dir0 = handle0_pos - pos0_lifted
approach_dir0[2] = 0  # ignore height difference for direction
approach_dir0 = approach_dir0 / np.linalg.norm(approach_dir0)

approach_dir1 = handle1_pos - pos1_lifted
approach_dir1[2] = 0
approach_dir1 = approach_dir1 / np.linalg.norm(approach_dir1)

# Define desired gripper orientations: sideways grasp, fingers opening along approach direction, gripper y-axis upward (aligned with world z)
# This means:
#   gripper forward (-z) should be aligned with approach direction
#   gripper y-axis should be aligned with world z-axis (0,0,1)

def vec_to_quat(forward, up):
    """Convert forward and up vectors to WXYZ quaternion."""
    # forward: direction gripper -z points (i.e., into the handle)
    # up: direction gripper y-axis points (should be world z)
    right = np.cross(up, forward)
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    rot_matrix = np.column_stack([right, up, forward])  # rotation matrix
    # Convert rotation matrix to quaternion
    trace = np.trace(rot_matrix)
    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2
        w = 0.25 * s
        x = (rot_matrix[2, 1] - rot_matrix[1, 2]) / s
        y = (rot_matrix[0, 2] - rot_matrix[2, 0]) / s
        z = (rot_matrix[1, 0] - rot_matrix[0, 1]) / s
    else:
        if rot_matrix[0, 0] > rot_matrix[1, 1] and rot_matrix[0, 0] > rot_matrix[2, 2]:
            s = np.sqrt(1.0 + rot_matrix[0, 0] - rot_matrix[1, 1] - rot_matrix[2, 2]) * 2
            w = (rot_matrix[2, 1] - rot_matrix[1, 2]) / s
            x = 0.25 * s
            y = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
            z = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
        elif rot_matrix[1, 1] > rot_matrix[2, 2]:
            s = np.sqrt(1.0 + rot_matrix[1, 1] - rot_matrix[0, 0] - rot_matrix[2, 2]) * 2
            w = (rot_matrix[0, 2] - rot_matrix[2, 0]) / s
            x = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
            y = 0.25 * s
            z = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
        else:
            s = np.sqrt(1.0 + rot_matrix[2, 2] - rot_matrix[0, 0] - rot_matrix[1, 1]) * 2
            w = (rot_matrix[1, 0] - rot_matrix[0, 1]) / s
            x = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
            y = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
            z = 0.25 * s
    return np.array([w, x, y, z])

# Normalize forward direction (gripper -z axis points along approach)
# Flip to negative because gripper's forward is usually -z
forward0 = -approach_dir0
forward1 = -approach_dir1
up_vec = np.array([0, 0, 1])  # world z-axis

quat0_grasp = vec_to_quat(forward0, up_vec)
quat1_grasp = vec_to_quat(forward1, up_vec)

# Slightly offset above handle for z_approach
approach_offset = 0.05

# Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach position above handles
goto_pose_both(
    handle0_pos + np.array([0, 0, approach_offset]), quat0_grasp,
    handle1_pos + np.array([0, 0, approach_offset]), quat1_grasp
)

# Now perform precise grasp with z_approach
goto_pose_both(
    handle0_pos, quat0_grasp,
    handle1_pos, quat1_grasp,
    z_approach=approach_offset
)

# Close both grippers to grasp handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift both arms to same height to lift the pot
lift_distance = 0.1
lift_pos0 = handle0_pos + np.array([0, 0, lift_distance])
lift_pos1 = handle1_pos + np.array([0, 0, lift_distance])

goto_pose_both(lift_pos0, quat0_grasp, lift_pos1, quat1_grasp)