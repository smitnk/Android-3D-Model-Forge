# Model report: Lizard Warrior

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `lizard_warrior` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.8854 m |
| Size (x, y, z) | [1.8293, 0.5754, 1.8854] m |
| Mesh parts | 4 |
| Vertices / triangles (GLB) | 33090 / 63976 |
| Materials | Bone, DrawingBack, DrawingFront |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 2237 KB |

## Checks

- ✅ `glb_exists_nonempty` out/lizard-warrior.glb
- ✅ `glb_structure_valid` 4 meshes, 33090 verts, 63976 tris
- ✅ `materials_present` Bone, DrawingBack, DrawingFront
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 2291060 bytes
- ✅ `expected_parts_present` 4 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.829, 0.575, 1.885) m
- ✅ `scale_usable` height 1.885 m (expected 0.5-3.0)
- ✅ `grounded` min z 0.0000
- ✅ `centered` center x 0.0000, y -0.0546
- ✅ `upright` height 1.885 > depth 0.575
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 0.97 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.146 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0292 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.206 vs width 0.256 (wide feet allowed), toe at y -0.090
- ✅ `geom_tpose_arm_R` forearm/hand 1.03 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.146 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0292 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.207 vs width 0.256 (wide feet allowed), toe at y -0.090
- ✅ `geom_left_right_symmetry` hand mirror error 0.00000 m
- ✅ `geom_head_size` head+neck above shoulders = 24% of height
- ✅ `geom_faces_forward` front-most head patch centred at x 0.000, y -0.228 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.829 m vs height 1.885 m
- ✅ `skin_in_glb` 1 skins, 6 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, -0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (0.0, -0.0, -1.0)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, -0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (-0.0, -0.0, -1.0)
