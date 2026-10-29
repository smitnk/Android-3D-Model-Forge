# Model report: Clay Chibi

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `clay_chibi` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.295 m |
| Size (x, y, z) | [0.9588, 0.4955, 1.295] m |
| Mesh parts | 2 |
| Vertices / triangles (GLB) | 14855 / 29702 |
| Materials | Clay |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 818 KB |

## Checks

- ✅ `glb_exists_nonempty` out/clay-chibi.glb
- ✅ `glb_structure_valid` 2 meshes, 14855 verts, 29702 tris
- ✅ `materials_present` Clay
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 838056 bytes
- ✅ `expected_parts_present` 2 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (0.959, 0.496, 1.295) m
- ✅ `scale_usable` height 1.295 m (expected 0.5-3.0)
- ✅ `grounded` min z -0.0000
- ✅ `centered` center x 0.0000, y -0.0128
- ✅ `upright` height 1.295 > depth 0.496
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 0.66 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.043 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0205 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.230 > width 0.150, toe at y -0.155
- ✅ `geom_tpose_arm_R` forearm/hand 1.29 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.042 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0210 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.230 > width 0.150, toe at y -0.155
- ✅ `geom_left_right_symmetry` hand mirror error 0.00096 m
- ✅ `geom_chibi_head` head+neck above shoulders = 49% of height
- ✅ `geom_faces_forward` front-most head point at x 0.004, y -0.261 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 0.959 m vs height 1.295 m
- ✅ `skin_in_glb` 1 skins, 2 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.116, -0.0, -0.993)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (-0.116, -0.0, -0.993)
