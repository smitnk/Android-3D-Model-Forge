# Model report: Round Buddy

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `round_buddy` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.2059 m |
| Size (x, y, z) | [1.3435, 0.456, 1.2059] m |
| Mesh parts | 2 |
| Vertices / triangles (GLB) | 33308 / 66252 |
| Materials | Face, Skin |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 1900 KB |

## Checks

- ✅ `glb_exists_nonempty` out/round-buddy.glb
- ✅ `glb_structure_valid` 2 meshes, 33308 verts, 66252 tris
- ✅ `materials_present` Face, Skin
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 1945272 bytes
- ✅ `expected_parts_present` 2 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.343, 0.456, 1.206) m
- ✅ `scale_usable` height 1.206 m (expected 0.5-3.0)
- ✅ `grounded` min z -0.0000
- ✅ `centered` center x 0.0000, y 0.0000
- ✅ `upright` height 1.206 > depth 0.456
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 0.41 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.097 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0120 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.288 vs width 0.160, toe at y -0.180
- ✅ `geom_tpose_arm_R` forearm/hand 0.41 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.097 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0105 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.288 vs width 0.160, toe at y -0.180
- ✅ `geom_left_right_symmetry` hand mirror error 0.00000 m
- ✅ `geom_head_size` head+neck above shoulders = 43% of height
- ✅ `geom_faces_forward` front-most head patch centred at x 0.000, y -0.223 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.343 m vs height 1.206 m
- ✅ `skin_in_glb` 1 skins, 3 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.06, -0.0, -0.998)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (-0.06, -0.0, -0.998)
