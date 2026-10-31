# Model report: Lizard Warrior Refined

**Validation: PASS** — 33/33 checks passed

| Property | Value |
|---|---|
| Generator | `lizard_refined` v0.2.0 |
| Blender | 4.2.3 LTS |
| Pose | T-pose (verified) |
| Height | 1.875 m |
| Size (x, y, z) | [1.8936, 0.7273, 1.875] m |
| Mesh parts | 5 |
| Vertices / triangles (GLB) | 111555 / 154860 |
| Materials | Armour000, Bone, Cloth000, Skin000, Skin030, Skin060, Skin090, Skin120, Skin150, Skin180, Skin210, Skin240, Skin270, Skin300, Skin330 |
| Rig | 17 bones, blended distance weights skinning |
| GLB size | 7448 KB |

## Checks

- ✅ `glb_exists_nonempty` out/lizard-warrior-refined.glb
- ✅ `glb_structure_valid` 5 meshes, 111555 verts, 154860 tris
- ✅ `materials_present` Armour000, Bone, Cloth000, Skin000, Skin030, Skin060, Skin090, Skin120, Skin150, Skin180, Skin210, Skin240, Skin270, Skin300, Skin330
- ✅ `materials_assigned` 0 primitives without material
- ✅ `size_reasonable` 7626408 bytes
- ✅ `expected_parts_present` 5 parts
- ✅ `geometry_finite` 
- ✅ `bbox_nonzero` size (1.894, 0.727, 1.875) m
- ✅ `scale_usable` height 1.875 m (expected 0.5-3.0)
- ✅ `grounded` min z -0.0000
- ✅ `centered` center x -0.0001, y 0.0213
- ✅ `upright` height 1.875 > depth 0.727
- ✅ `no_degenerate_parts` 
- ✅ `geom_tpose_arm_L` forearm/hand 4.66 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_L` arm band vertical thickness 0.113 m
- ✅ `geom_leg_vertical_L` leg centre drift 0.0104 m between lower and upper leg
- ✅ `geom_foot_forward_L` foot length 0.312 vs width 0.206 (wide feet allowed), toe at y -0.053
- ✅ `geom_tpose_arm_R` forearm/hand 4.63 deg from horizontal vs upper arm (max 8.0)
- ✅ `geom_arm_is_limb_R` arm band vertical thickness 0.113 m
- ✅ `geom_leg_vertical_R` leg centre drift 0.0101 m between lower and upper leg
- ✅ `geom_foot_forward_R` foot length 0.310 vs width 0.205 (wide feet allowed), toe at y -0.053
- ✅ `geom_left_right_symmetry` hand mirror error 0.00128 m
- ✅ `geom_head_size` head+neck above shoulders = 25% of height
- ✅ `geom_faces_forward` front-most head patch centred at x -0.000, y -0.227 (Blender -Y = glTF +Z front)
- ✅ `geom_tpose_span` span 1.894 m vs height 1.875 m
- ✅ `skin_in_glb` 1 skins, 16 skinned primitives
- ✅ `armature_present` 1 armatures
- ✅ `expected_bones` 17 bones
- ✅ `meshes_bound_to_armature` all meshes skinned
- ✅ `rest_pose_arm_bones_horizontal_L` upper_arm->hand dir (1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_L` thigh->foot dir (-0.0, -0.0, -1.0)
- ✅ `rest_pose_arm_bones_horizontal_R` upper_arm->hand dir (-1.0, 0.0, 0.0)
- ✅ `rest_pose_leg_bones_vertical_R` thigh->foot dir (0.0, -0.0, -1.0)
