# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

# First, get the grasp pose for the extruded handle of the brown square nut
handle_position, handle_quaternion_wxyz = sample_grasp_pose('extruded handle of the brown square nut')

# Approach and grasp the handle of the nut
goto_pose(handle_position, handle_quaternion_wxyz, z_approach=0.1)  # approach from 10cm above
goto_pose(handle_position, handle_quaternion_wxyz)  # move down to grasp pose
close_gripper()  # grasp the nut by its handle

# Now, get the center of the nut (white hollow center) to understand the relative transform
center_position, center_quaternion_wxyz = get_object_pose('white hollow center of the brown square nut')

# Compute the fixed rigid transform from handle grasp pose to nut center
# This will allow us to compute where the center would be during insertion
handle_rot = Rotation.from_quat(handle_quaternion_wxyz)
center_rot = Rotation.from_quat(center_quaternion_wxyz)

# Transform from handle to center in the object's local frame
local_handle_to_center = handle_rot.inv().apply(center_position - handle_position)
local_handle_to_center_rot = handle_rot.inv() * center_rot

# Now, get the pose of the brown square block (target peg location)
block_position, block_quaternion_wxyz = get_object_pose('brown square block')
target_center_position = block_position
target_center_rotation = Rotation.from_quat(block_quaternion_wxyz)

# Compute desired handle pose during insertion using the inverse of the local transform
desired_handle_position = target_center_position - target_center_rotation.apply(local_handle_to_center)
desired_handle_rotation = target_center_rotation * local_handle_to_center_rot.inv()
desired_handle_quaternion_wxyz = desired_handle_rotation.as_quat()  # returns (x, y, z, w)

# Move above the insertion point with z_approach to avoid collision
goto_pose(desired_handle_position, desired_handle_quaternion_wxyz, z_approach=0.1)

# Perform the insertion motion slowly
goto_pose(desired_handle_position, desired_handle_quaternion_wxyz)

# Optionally: wiggle or pause slightly to ensure insertion
# (no API for this, so we assume precise motion is enough)

# Open gripper to release the nut
open_gripper()

# Return to home position
goto_home_joint_position()