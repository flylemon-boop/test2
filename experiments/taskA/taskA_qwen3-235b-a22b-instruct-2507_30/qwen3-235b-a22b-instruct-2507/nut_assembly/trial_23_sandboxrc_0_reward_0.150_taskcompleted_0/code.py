# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

# First, get the grasp pose for the extruded handle of the brown square nut
handle_position, handle_quaternion_wxyz = sample_grasp_pose('extruded handle of the brown square nut')

# Approach and grasp the handle of the nut
goto_pose(handle_position, handle_quaternion_wxyz, z_approach=0.1)  # approach from 10cm above
goto_pose(handle_position, handle_quaternion_wxyz)  # move to actual grasp pose
close_gripper()  # close gripper to grasp the nut

# Now, get the center of the brown square block (target insertion point)
block_center_position, block_center_quaternion_wxyz = get_object_pose('white hollow center of the brown square block')

# Compute the fixed offset between the handle grasp pose and the nut's center
# We need to apply this same offset when inserting so that the nut aligns correctly with the block
nut_center_position, _ = get_object_pose('white hollow center of the brown square nut')
offset_from_handle_to_nut_center = nut_center_position - handle_position

# Desired final position: block center position but adjusted by the inverse of the offset
insertion_position = block_center_position - offset_from_handle_to_nut_center

# Use the rotation of the block center for proper alignment during insertion
insertion_quaternion_wxyz = block_center_quaternion_wxyz

# Perform insertion motion
goto_pose(insertion_position, insertion_quaternion_wxyz, z_approach=0.1)  # approach from above
goto_pose(insertion_position, insertion_quaternion_wxyz)  # insert

# Open gripper to release the nut
open_gripper()

# Return arm to home position
goto_home_joint_position()