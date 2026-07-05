# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

# Lift arms up by 0.1 meters in Z
lift_offset = np.array([0.0, 0.0, 0.1])
goto_pose_arm0(pos0 + lift_offset, quat0)
goto_pose_arm1(pos1 + lift_offset, quat1)

# Get handle positions from vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define grasp orientation: gripper y-axis aligned with world z-axis (sideways grasp)
# Desired rotation matrix:
# x-axis points towards the pot center (from handle to center), y-axis = world z-axis, z-axis perpendicular
world_z = np.array([0, 0, 1])

# For Arm 0 (handle0): x-axis points inward (towards center), so -x direction
inward0 = - (handle1_pos - handle0_pos)  # approximates direction from handle0 to center
inward0[2] = 0  # keep horizontal
x0 = -inward0 / np.linalg.norm(inward0)
z0 = np.cross(x0, world_z)
y0 = np.cross(z0, x0)
rotmat0 = np.column_stack([x0, y0, z0])

# Convert rotation matrix to quaternion [w, x, y, z]
trace = np.trace(rotmat0)
if trace > 0:
    s = 0.5 / np.sqrt(trace + 1.0)
    w = 0.25 / s
    x = (rotmat0[2, 1] - rotmat0[1, 2]) * s
    y = (rotmat0[0, 2] - rotmat0[2, 0]) * s
    z = (rotmat0[1, 0] - rotmat0[0, 1]) * s
else:
    if rotmat0[0, 0] > rotmat0[1, 1] and rotmat0[0, 0] > rotmat0[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotmat0[0, 0] - rotmat0[1, 1] - rotmat0[2, 2])
        w = (rotmat0[2, 1] - rotmat0[1, 2]) / s
        x = 0.25 * s
        y = (rotmat0[0, 1] + rotmat0[1, 0]) / s
        z = (rotmat0[0, 2] + rotmat0[2, 0]) / s
    elif rotmat0[1, 1] > rotmat0[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotmat0[1, 1] - rotmat0[0, 0] - rotmat0[2, 2])
        w = (rotmat0[0, 2] - rotmat0[2, 0]) / s
        x = (rotmat0[0, 1] + rotmat0[1, 0]) / s
        y = 0.25 * s
        z = (rotmat0[1, 2] + rotmat0[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + rotmat0[2, 2] - rotmat0[0, 0] - rotmat0[1, 1])
        w = (rotmat0[1, 0] - rotmat0[0, 1]) / s
        x = (rotmat0[0, 2] + rotmat0[2, 0]) / s
        y = (rotmat0[1, 2] + rotmat0[2, 1]) / s
        z = 0.25 * s
quat0_grasp = np.array([w, x, y, z])

# For Arm 1 (handle1): x-axis points inward (towards center)
inward1 = handle1_pos - handle0_pos
inward1[2] = 0
x1 = -inward1 / np.linalg.norm(inward1)
z1 = np.cross(x1, world_z)
y1 = np.cross(z1, x1)
rotmat1 = np.column_stack([x1, y1, z1])

# Convert rotation matrix to quaternion for arm1
trace = np.trace(rotmat1)
if trace > 0:
    s = 0.5 / np.sqrt(trace + 1.0)
    w = 0.25 / s
    x = (rotmat1[2, 1] - rotmat1[1, 2]) * s
    y = (rotmat1[0, 2] - rotmat1[2, 0]) * s
    z = (rotmat1[1, 0] - rotmat1[0, 1]) * s
else:
    if rotmat1[0, 0] > rotmat1[1, 1] and rotmat1[0, 0] > rotmat1[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotmat1[0, 0] - rotmat1[1, 1] - rotmat1[2, 2])
        w = (rotmat1[2, 1] - rotmat1[1, 2]) / s
        x = 0.25 * s
        y = (rotmat1[0, 1] + rotmat1[1, 0]) / s
        z = (rotmat1[0, 2] + rotmat1[2, 0]) / s
    elif rotmat1[1, 1] > rotmat1[2, 2]:
        s = 2.0 * np.sqrt(1.0 + rotmat1[1, 1] - rotmat1[0, 0] - rotmat1[2, 2])
        w = (rotmat1[0, 2] - rotmat1[2, 0]) / s
        x = (rotmat1[0, 1] + rotmat1[1, 0]) / s
        y = 0.25 * s
        z = (rotmat1[1, 2] + rotmat1[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + rotmat1[2, 2] - rotmat1[0, 0] - rotmat1[1, 1])
        w = (rotmat1[1, 0] - rotmat1[0, 1]) / s
        x = (rotmat1[0, 2] + rotmat1[2, 0]) / s
        y = (rotmat1[1, 2] + rotmat1[2, 1]) / s
        z = 0.25 * s
quat1_grasp = np.array([w, x, y, z])

# Use approach distance to safely descend onto handle
approach_dist = 0.05  # 5 cm above

# Move both arms simultaneously to approach poses
goto_pose_both(
    position0=handle0_pos + np.array([0, 0, approach_dist]),
    quaternion_wxyz0=quat0_grasp,
    position1=handle1_pos + np.array([0, 0, approach_dist]),
    quaternion_wxyz1=quat1_grasp,
    z_approach=0.0
)

# Descend and grasp both handles
goto_pose_both(
    position0=handle0_pos,
    quaternion_wxyz0=quat0_grasp,
    position1=handle1_pos,
    quaternion_wxyz1=quat1_grasp,
    z_approach=0.0
)

# Close both grippers
close_gripper_arm0()
close_gripper_arm1()

# Lift the pot up together by 0.2 meters
lift_height = 0.2
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(
    position0=final_pos0,
    quaternion_wxyz0=quat0_grasp,
    position1=final_pos1,
    quaternion_wxyz1=quat1_grasp,
    z_approach=0.0
)