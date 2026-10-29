# Model report: Snow Buddy

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `snow_buddy` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.1699 m |
| Size (x, y, z) | [1.0798, 0.4629, 1.1699] m |
| Mesh parts | 8 |
| Vertices / triangles (GLB) | 80090 / 160152 |
| Materials | CoolRim, FaceBlack, SnowWhite, TongueRed |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 4392 KB |

## Checks

- ✅ `glb_exists_nonempty` out/snow-buddy.glb
- ✅ `glb_structure_valid` 8 meshes, 80090 verts, 160152 tris
- ✅ `materials_present` CoolRim, FaceBlack, SnowWhite, TongueRed
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 4497736 bytes
- ✅ `expected_parts_present` 8 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.08, 0.463, 1.17) m
- ✅ `scale_usable` height 1.170 m (expected 0.5-3.0)
- ✅ `grounded` min z 0.0000
- ✅ `centered` center x 0.0000, y -0.0085
- ✅ `upright` height 1.170 > depth 0.463
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 0.60 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.090 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0081 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.246 vs width 0.142, toe at y -0.177
- ✅ `geom_tpose_arm_R` forearm/hand 0.60 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.090 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0084 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.246 vs width 0.142, toe at y -0.177
- ✅ `geom_left_right_symmetry` hand mirror error 0.00000 m
- ✅ `geom_head_size` head+neck above shoulders = 47% of height
- ✅ `geom_faces_forward` front-most head patch centred at x -0.000, y -0.236 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.080 m vs height 1.170 m
- ✅ `skin_in_glb` 1 skins, 8 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.035, -0.0, -0.999)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (-0.035, -0.0, -0.999)
