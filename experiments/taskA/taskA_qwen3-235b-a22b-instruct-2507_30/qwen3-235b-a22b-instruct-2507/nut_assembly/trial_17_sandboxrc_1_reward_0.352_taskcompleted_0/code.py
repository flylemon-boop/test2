# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

# First, get the pose for grasping the extruded handle of the brown square nut
handle_position, handle_quaternion = sample_grasp_pose('extruded handle of the brown square nut')

# Approach and grasp the handle
goto_pose(handle_position, handle_quaternion, z_approach=0.1)  # approach from 10cm above
goto_pose(handle_position, handle_quaternion)  # move to grasp pose
close_gripper()  # close gripper to grasp the nut

# Now get the center of the brown square nut (white hollow center) to determine its orientation relative to the handle
center_position, center_quaternion = get_object_pose('white hollow center of the brown square nut')

# Compute the fixed transform between the handle grasp pose and the nut's center
# This will allow us to track how the nut is oriented once we're holding it by the handle
rel_rot_matrix = Rotation.from_quat(center_quaternion).as_matrix() @ Rotation.from_quat(handle_quaternion).inv().as_matrix()
rel_translation = center_position - handle_position

# Get the pose of the brown square block where we want to insert the nut
block_position, block_quaternion = get_object_pose('brown square block')

# Desired final pose: align nut center with block position, using block orientation
final_center_position = block_position
final_center_quaternion = block_quaternion

# Now compute the corresponding end-effector pose (i.e., handle pose) based on the fixed transform
# Apply inverse rigid transform: from center -> handle
final_handle_rotation = Rotation.from_quat(final_center_quaternion) * Rotation.from_quat(rel_rot_matrix)
final_handle_quaternion = final_handle_rotation.as_quat()

final_handle_position = final_center_position - (Rotation.from_quat(final_handle_quaternion).as_matrix() @ rel_translation)

# Move to insertion pose with approach from above
goto_pose(final_handle_position, final_handle_quaternion, z_approach=0.1)
goto_pose(final_handle_position, final_handle_quaternion)

# Open gripper to release the nut
open_gripper()

# Return to home joint configuration
goto_home_joint_position()