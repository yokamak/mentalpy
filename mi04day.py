import mentalpy

# 🧱 [準備] mental ray を動かすインターフェースを立ち上げます
mi = mentalpy.MentalRayInterface()
mi.SetOptions()

# =========================================================================
# 🌤️ 物理的な太陽光・空・カメラフィルター（Daylightシステム）の定義
# =========================================================================
# 💡 カメラ定義より前に配置して「未定義エラー」を回避します

# ① 物理的な太陽光（mia_physicalsun）
sun_light_def = (
    'light "sunShape"\n'
    '    "mia_physicalsun" (\n'
    '        "on" on,\n'
    '        "multiplier" 1.0,\n'
    '        "y_is_up" on,\n'
    '        "rgb_unit_conversion" 0.0001 0.0001 0.0001\n'
    '    )\n'
    '    direction -1. -1. -1.\n'
    'end light\n'
)
mi.commands.append(sun_light_def)

# ② 太陽のインスタンス（配置用スタンド）
sun_instance_def = (
    'instance "sunDirection" "sunShape"\n'
    '    transform\n'
    '        1. 0. 0. 0.\n'
    '        0. 1. 0. 0.\n'
    '        0. 0. 1. 0.\n'
    '        0. 0. 0. 1.\n'
    'end instance\n'
)
mi.commands.append(sun_instance_def)
mi.instgroup_members.append("sunDirection")

# ③ 露出調整フィルター（mia_exposure_simple）
exposure_shader_def = (
    'shader "mia_exposure_simple1"\n'
    '    "mia_exposure_simple" (\n'
    '        "pedestal" 0.,\n'
    '        "gain" 0.18,\n'
    '        "knee" 0.75,\n'
    '        "compression" 3.,\n'
    '        "gamma" 2.2,\n'
    '        "use_preview" off\n'
    '    )\n'
)
mi.commands.append(exposure_shader_def)

# ④ 物理的な青空背景（mia_physicalsky）
physical_sky_def = (
    'shader "mia_physicalsky1"\n'
    '    "mia_physicalsky" (\n'
    '        "on" on,\n'
    '        "multiplier" 0.5,\n'
    '        "rgb_unit_conversion" 0.0001 0.0001 0.0001 1.,\n'
    '        "haze" 0.,\n'
    '        "redblueshift" -0.3,\n'
    '        "saturation" 1.,\n'
    '        "horizon_height" -2.5,\n'
    '        "horizon_blur" 0.1,\n'
    '        "ground_color" 0.2 0.2 0.2 1.,\n'
    '        "night_color" 0. 0. 0. 1.,\n'
    '        "sun_direction" 0. 0. 0.,\n'
    '        "sun" "sunDirection",\n'
    '        "sun_disk_intensity" 1.,\n'
    '        "sun_disk_scale" 4.,\n'
    '        "sun_glow_intensity" 1.,\n'
    '        "use_background" off,\n'
    '        "visibility_distance" 0.,\n'
    '        "y_is_up" on\n'
    '    )\n'
)
mi.commands.append(physical_sky_def)


# =========================================================================
# 1. カメラ設定（解像度 800x600）
# =========================================================================
mi.NewCameraLookAt(
    name="cam",
    pos=[0.0, 20.0, -55.0],
    target=[0.0, 5.0, 0.0],
    filename="mi04day_mia.tif"
)


# =========================================================================
# 2. ライト設定
# =========================================================================
mi.NewLightLookAt(
    name="env_light",
    pos=[-50.0, 100.0, -50.0],
    target=[0.0, 0.0, 0.0],
    color=[0.8, 0.8, 0.8]
)


# =========================================================================
# 3. マテリアル・ジオメトリ定義
# =========================================================================
# 地面用マテリアル
ground_material = (
    'material "white_matte"\n'
    '    "mib_illum_phong" (\n'
    '        "ambient" 0.1 0.1 0.1,\n'
    '        "diffuse" 0.7 0.7 0.7,\n'
    '        "specular" 0.1 0.1 0.1,\n'
    '        "exponent" 10.0,\n'
    '        "lights" ["env_light_inst"]\n'
    '    )\n'
    'end material\n'
)
mi.commands.append(ground_material)

# 物理マテリアル（mia_material_x）
mia_mat_def = (
    'material "mia_material_x1"\n'
    '    "mia_material_x" (\n'
    '        "diffuse_weight" 1.,\n'
    '        "diffuse" 0.772 0.153565 0.148996 1.,\n'
    '        "diffuse_roughness" 0.,\n'
    '        "reflectivity" 0.6,\n'
    '        "refl_color" 1. 1. 1. 1.,\n'
    '        "refl_gloss" 1.,\n'
    '        "refl_gloss_samples" 8,\n'
    '        "refl_interpolate" off,\n'
    '        "refl_hl_only" off,\n'
    '        "refl_is_metal" off,\n'
    '        "transparency" 0.,\n'
    '        "refr_color" 1. 1. 1. 1.,\n'
    '        "refr_gloss" 1.,\n'
    '        "refr_ior" 1.4,\n'
    '        "refr_gloss_samples" 8,\n'
    '        "refr_interpolate" off,\n'
    '        "refr_translucency" off,\n'
    '        "refr_trans_color" 0.7 0.6 0.5 1.,\n'
    '        "refr_trans_weight" 0.5,\n'
    '        "anisotropy" 1.,\n'
    '        "anisotropy_rotation" 0.,\n'
    '        "anisotropy_channel" -1,\n'
    '        "brdf_fresnel" off,\n'
    '        "brdf_0_degree_refl" 0.2,\n'
    '        "brdf_90_degree_refl" 1.,\n'
    '        "brdf_curve" 5.,\n'
    '        "brdf_conserve_energy" on,\n'
    '        "intr_grid_density" 2,\n'
    '        "intr_refl_samples" 2,\n'
    '        "intr_refl_ddist_on" off,\n'
    '        "intr_refl_ddist" 0.,\n'
    '        "intr_refr_samples" 2,\n'
    '        "single_env_sample" off,\n'
    '        "refl_falloff_on" off,\n'
    '        "refl_falloff_dist" 0.,\n'
    '        "refl_falloff_color_on" off,\n'
    '        "refl_falloff_color" 0. 0. 0. 1.,\n'
    '        "refl_depth" 5,\n'
    '        "refl_cutoff" 0.01,\n'
    '        "refr_falloff_on" off,\n'
    '        "refr_falloff_dist" 0.,\n'
    '        "refr_falloff_color_on" off,\n'
    '        "refr_falloff_color" 0. 0. 0. 1.,\n'
    '        "refr_depth" 5,\n'
    '        "refr_cutoff" 0.01,\n'
    '        "indirect_multiplier" 1.,\n'
    '        "fg_quality" 1.,\n'
    '        "fg_quality_w" 1.,\n'
    '        "ao_on" off,\n'
    '        "ao_samples" 16,\n'
    '        "ao_distance" 10.,\n'
    '        "ao_dark" 0.2 0.2 0.2 1.,\n'
    '        "ao_ambient" 0. 0. 0. 1.,\n'
    '        "ao_do_details" 1,\n'
    '        "thin_walled" off,\n'
    '        "no_visible_area_hl" on,\n'
    '        "skip_inside_refl" on,\n'
    '        "do_refractive_caustics" off,\n'
    '        "backface_cull" off,\n'
    '        "propagate_alpha" off,\n'
    '        "hl_vs_refl_balance" 1.,\n'
    '        "cutout_opacity" 1.,\n'
    '        "additional_color" 0. 0. 0. 1.,\n'
    '        "no_diffuse_bump" off,\n'
    '        "mode" 4,\n'
    '        "lights" [],\n'
    '        "bump_mode" 5,\n'
    '        "overall_bump" 0. 0. 0.,\n'
    '        "standard_bump" 0. 0. 0.,\n'
    '        "multiple_outputs" on\n'
    '    )\n'
    'end material\n'
)
mi.commands.append(mia_mat_def)

# 球体ジオメトリの読み込み
mi.AddBaseSphereObject()

# 平面ジオメトリ（p "" にしてインスタンスから割り当て可能に設定）
ground_geo = (
    'object "ground_geo" visible trace shadow tag 1\n'
    '    group\n'
    '        -50.0  0  -50.0\n'
    '        -50.0  0   50.0\n'
    '         50.0  0  -50.0\n'
    '         50.0  0   50.0\n'
    '        v 0  v 1  v 2  v 3\n'
    '        p "" 0 1 3 2\n'
    '    end group\n'
    'end object\n'
)
mi.commands.append(ground_geo)


# =========================================================================
# 4. 配置（インスタンス化）
# =========================================================================
# 地面の配置
mi.NewInstance(
    "ground_inst", "ground_geo", "white_matte",
    matrix=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
)

# 球体の配置（mia_material_x1 を適用）
mi.NewObjectInstance("sphere_inst", "sphere_geo", "mia_material_x1")
mi.SetProperty3("sphere_inst", 'translate', 0, 5, 0)
mi.SetProperty3("sphere_inst", 'scale',     1, 1, 1)
mi.SetProperty3("sphere_inst", 'rotate',    0, 0, 0)


# =========================================================================
# ⚙️ カメラへのシェーダー装着と実行
# =========================================================================
# 生成されたカメラ定義にレンズシェーダーと環境シェーダーをドッキング
for idx, cmd in enumerate(mi.commands):
    if 'camera "cam"' in cmd:
        mi.commands[idx] = cmd.replace(
            'end camera',
            '    lens = "mia_exposure_simple1"\n    environment = "mia_physicalsky1"\nend camera'
        )

mi.FlushInstances()
mi.Run()