# Model report: Gorilla

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `gorilla` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.4803 m |
| Size (x, y, z) | [1.5842, 0.4554, 1.4803] m |
| Mesh parts | 11 |
| Vertices / triangles (GLB) | 20532 / 41000 |
| Materials | EyeWhite, Fur, Nostril, Pupil, Skin |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 1136 KB |

## Checks

- ✅ `glb_exists_nonempty` out/gorilla.glb
- ✅ `glb_structure_valid` 11 meshes, 20532 verts, 41000 tris
- ✅ `materials_present` EyeWhite, Fur, Nostril, Pupil, Skin
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 1163544 bytes
- ✅ `expected_parts_present` 8 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.584, 0.455, 1.48) m
- ✅ `scale_usable` height 1.480 m (expected 0.5-3.0)
- ✅ `grounded` min z -0.0000
- ✅ `centered` center x -0.0000, y -0.0108
- ✅ `upright` height 1.480 > depth 0.455
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 1.65 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.157 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0177 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.323 > width 0.322, toe at y -0.229
- ✅ `geom_tpose_arm_R` forearm/hand 2.44 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.157 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0187 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.323 > width 0.322, toe at y -0.229
- ✅ `geom_left_right_symmetry` hand mirror error 0.00084 m
- ✅ `geom_head_size` head+neck above shoulders = 29% of height
- ✅ `geom_faces_forward` front-most head point at x 0.011, y -0.227 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.584 m vs height 1.480 m
- ✅ `skin_in_glb` 1 skins, 11 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.048, -0.0, -0.999)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (-0.048, -0.0, -0.999)
