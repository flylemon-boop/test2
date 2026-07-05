# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

lift_height = 0.1  # Lift 10 cm up
pos0_lifted = pos0.copy()
pos0_lifted[2] += lift_height
pos1_lifted = pos1.copy()
pos1_lifted[2] += lift_height

goto_pose_both(pos0_lifted, quat0, pos1_lifted, quat1, z_approach=0.0)

# Get handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis
# Desired rotation: align gripper frame such that:
#   x-axis points into the handle (horizontally)
#   y-axis points upward (aligned with world z)
#   z-axis completes the right-hand rule (horizontal, perpendicular to x and y)
# This corresponds to a quaternion that rotates from canonical [x,y,z] -> [-z,x,y] or similar depending on gripper mounting.

# We'll construct a rotation matrix and convert to quaternion.
# For arm0 (on one side), we want approach along -x direction, y aligned with world +z.
forward0 = -np.array([1, 0, 0])  # Arm0 approaches along negative x
left0 = np.array([0, 0, 1])      # Gripper y-axis points up (world z)
up0 = np.cross(forward0, left0)   # Complete the frame

R0 = np.column_stack((forward0, left0, up0))

# For arm1 (opposite side), approach along +x direction, y still aligned with world +z
forward1 = np.array([1, 0, 0])   # Arm1 approaches along positive x
left1 = np.array([0, 0, 1])      # Gripper y-axis points up
up1 = np.cross(forward1, left1)

R1 = np.column_stack((forward1, left1, up1))

# Convert rotation matrices to quaternions
def rotmat_to_quat(R):
    trace = np.trace(R)
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
    return np.array([w, x, y, z])

quat0_grasp = rotmat_to_quat(R0)
quat1_grasp = rotmat_to_quat(R1)

# Normalize quaternions
quat0_grasp /= np.linalg.norm(quat0_grasp)
quat1_grasp /= np.linalg.norm(quat1_grasp)

# Approach each handle from the side with z_approach to ensure safe descent
approach_offset = 0.05  # 5 cm above the handle for initial approach

# Prepare approach poses
approach0 = handle0_pos.copy()
approach0[2] += approach_offset
approach1 = handle1_pos.copy()
approach1[2] += approach_offset

# Move both arms to approach poses
goto_pose_both(approach0, quat0_grasp, approach1, quat1_grasp, z_approach=0.0)

# Now move down to grasp poses with z_approach to ensure precise motion
goto_pose_both(handle0_pos, quat0_grasp, handle1_pos, quat1_grasp, z_approach=approach_offset)

# Close both grippers simultaneously
close_gripper_arm0()
close_gripper_arm1()

# Lift the pot together to same height
lift_z = 0.2  # Lift 20 cm up from current position
target0_lift = handle0_pos + np.array([0, 0, lift_z])
target1_lift = handle1_pos + np.array([0, 0, lift_z])

goto_pose_both(target0_lift, quat0_grasp, target1_lift, quat1_grasp, z_approach=0.0)