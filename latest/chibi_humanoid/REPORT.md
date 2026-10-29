# Model report: Forge Kid

**Validation: PASS** — 47/47 checks passed

| Property | Value |
|---|---|
| Generator | `chibi_humanoid` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.3448 m |
| Size (x, y, z) | [1.1191, 0.5541, 1.3448] m |
| Mesh parts | 42 |
| Vertices / triangles (GLB) | 12378 / 24588 |
| Materials | Brow, EyeWhite, Hair, Mouth, Pupil, Shirt, Shoe, Shorts, Skin, Sole |
| Rig | 17 bones, rigid per-part skinning |
| GLB size | 654 KB |

## Checks

- ✅ `glb_exists_nonempty` out/forge-kid.glb
- ✅ `glb_structure_valid` 42 meshes, 12378 verts, 24588 tris
- ✅ `materials_present` Brow, EyeWhite, Hair, Mouth, Pupil, Shirt, Shoe, Shorts, Skin, Sole
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 669336 bytes
- ✅ `expected_parts_present` 27 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.119, 0.554, 1.345) m
- ✅ `scale_usable` height 1.345 m (expected 0.5-3.0)
- ✅ `grounded` min z 0.0001
- ✅ `centered` center x 0.0000, y 0.0220
- ✅ `upright` height 1.345 > depth 0.554
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 0.26 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.082 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0029 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.215 > width 0.118, toe at y -0.137
- ✅ `geom_tpose_arm_R` forearm/hand 0.26 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.082 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0039 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.215 > width 0.118, toe at y -0.137
- ✅ `geom_left_right_symmetry` hand mirror error 0.00000 m
- ✅ `geom_head_size` head+neck above shoulders = 52% of height
- ✅ `geom_faces_forward` front-most head point at x -0.000, y -0.255 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.119 m vs height 1.345 m
- ✅ `tpose_arm_horizontal_L` arm angle 0.00 deg from horizontal (max 8.0)
- ✅ `tpose_upperarm_along_x_L` x-extent 0.210 vs z-extent 0.107
- ✅ `tpose_elbow_straight_L` forearm angle 0.00 deg
- ✅ `leg_straight_vertical_L` shin z/x 0.190/0.090, shin-shoe dx 0.0000
- ✅ `foot_points_forward_L` shoe depth 0.219 > width 0.119
- ✅ `tpose_arm_horizontal_R` arm angle 0.00 deg from horizontal (max 8.0)
- ✅ `tpose_upperarm_along_x_R` x-extent 0.210 vs z-extent 0.107
- ✅ `tpose_elbow_straight_R` forearm angle 0.00 deg
- ✅ `leg_straight_vertical_R` shin z/x 0.190/0.090, shin-shoe dx 0.0000
- ✅ `foot_points_forward_R` shoe depth 0.219 > width 0.119
- ✅ `tpose_arm_span` span 1.119 m vs height 1.345 m
- ✅ `left_right_symmetry` max mirror error 0.00000 m
- ✅ `faces_forward` nose y -0.240 in front of head centre y 0.000 (Blender -Y = glTF +Z front)
- ✅ `chibi_proportions` head is 37% of height
- ✅ `skin_in_glb` 1 skins, 42 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.0, -0.0, -1.0)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (0.0, -0.0, -1.0)
