# Model report: Gorilla

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `gorilla` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.4956 m |
| Size (x, y, z) | [2.3502, 0.67, 1.4956] m |
| Mesh parts | 1 |
| Vertices / triangles (GLB) | 46386 / 90784 |
| Materials | DrawingBack, DrawingFront |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 3098 KB |

## Checks

- ✅ `glb_exists_nonempty` out/gorilla.glb
- ✅ `glb_structure_valid` 1 meshes, 46386 verts, 90784 tris
- ✅ `materials_present` DrawingBack, DrawingFront
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 3172796 bytes
- ✅ `expected_parts_present` 1 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (2.35, 0.67, 1.496) m
- ✅ `scale_usable` height 1.496 m (expected 0.5-3.0)
- ✅ `grounded` min z 0.0000
- ✅ `centered` center x 0.0000, y 0.0000
- ✅ `upright` height 1.496 > depth 0.670
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 3.58 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.282 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0321 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.243 vs width 0.343 (wide feet allowed), toe at y -0.092
- ✅ `geom_tpose_arm_R` forearm/hand 3.58 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.282 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0321 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.243 vs width 0.343 (wide feet allowed), toe at y -0.092
- ✅ `geom_left_right_symmetry` hand mirror error 0.00000 m
- ✅ `geom_head_size` head+neck above shoulders = 37% of height
- ✅ `geom_faces_forward` front-most head patch centred at x -0.000, y -0.333 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 2.350 m vs height 1.496 m
- ✅ `skin_in_glb` 1 skins, 2 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (-0.0, -0.0, -1.0)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (0.0, -0.0, -1.0)
