import mentalpy
import random

random.seed(42)

si = mentalpy.MentalRayInterface()
si.SetOptions()

si.NewCameraLookAt(
    name="cam",
    pos=[0.0, 50.0, -120.0],
    target=[0.0, 0.0, 0.0],
    filename="mi03grid.tif"
)
si.NewLightLookAt(
    name="env_light",
    pos=[-60.0, 120.0, -60.0],
    target=[0.0, 0.0, 0.0],
    color=[1.3, 1.3, 1.3]
)
si.NewRedPlasticMaterial("red_plastic", light_inst_name="env_light_inst")

si.commands.append(
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

# 地面 Y=-5
si.commands.append(
    'object "ground_geo" visible trace shadow tag 1\n'
    '    group\n'
    '        -200.0  -5.0  -200.0\n'
    '        -200.0  -5.0   200.0\n'
    '         200.0  -5.0  -200.0\n'
    '         200.0  -5.0   200.0\n'
    '        v 0  v 1  v 2  v 3\n'
    '        p "white_matte" 0 1 3 2\n'
    '    end group\n'
    'end object\n'
)
si.commands.append('shader "green_mia" "mia_material_x" (\n'
        '"diffuse_weight" 1.0,\n'
        '"diffuse" 0.7 0.9 0.7 1.0,      # 白〜明るいグレー\n'
        '"reflectivity" 0.6,             # 反射率を最大（100%）に\n'
        '"refl_color" 1.0 1.0 1.0 1.0,\n'
        '"refl_gloss" 1.0,               # 1.0で完全に滑らかな鏡面になる\n'
        '"refl_is_metal" off,             # ★金属モードはON\n'
        '"brdf_fresnel" on,\n'
        '"lights" ["env_light_inst"]    # ※シーンのライトインスタンス名に合わせてください\n'
    ')\n'
'material "green_plastic" = "green_mia" shadow = "green_mia" photon = "green_mia" end material\n'
)


# 原点中心 Cube: -5〜+5（コメント行なし）
si.commands.append(
    'object "cube_geo" visible trace shadow tag 2\n'
    '    group\n'
    '        -5 -5 -5\n'
    '         5 -5 -5\n'
    '        -5 -5  5\n'
    '         5 -5  5\n'
    '        -5  5 -5\n'
    '         5  5 -5\n'
    '        -5  5  5\n'
    '         5  5  5\n'
    '        v 0 v 1 v 2 v 3 v 4 v 5 v 6 v 7\n'
    '        p "" 0 1 5 4\n'
    '        p "" 1 3 7 5\n'
    '        p "" 3 2 6 7\n'
    '        p "" 2 0 4 6\n'
    '        p "" 4 5 7 6\n'
    '        p "" 2 3 1 0\n'
    '    end group\n'
    'end object\n'
)

si.NewInstance(
    "ground_inst", "ground_geo", "white_matte",
    matrix=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
)

# ────────────────────────────────────────────────────────
# 3×3 グリッド
# 地面 Y=-5、Cube 半辺=5 → translate Y = -5+5 = 0 で底面が地面に揃う
# Y軸回転は Y 座標に影響しないので全9個とも ty=0 固定
# ────────────────────────────────────────────────────────
GRID     = 3
SPACING  = 25.0
GROUND_Y = -5.0
CUBE_HALF = 5.0

offset = (GRID - 1) * SPACING / 2.0   # = 25.0（グリッドを原点中心に揃える）

for row in range(GRID):
    for col in range(GRID):
        idx   = row * GRID + col
        tx    = col * SPACING - offset
        tz    = row * SPACING - offset
        ty    = GROUND_Y + CUBE_HALF    # -5 + 5 = 0
        rot_y = random.uniform(0, 360)

        name = f"cube_{idx:02d}"
        si.NewObjectInstance(name, 'cube_geo', 'green_plastic')
        si.SetProperty3(name, 'translate', tx, ty, tz)
        si.SetProperty3(name, 'scale',     1,  1,  1)
        si.SetProperty3(name, 'rotate',    0, rot_y, 0)

        print(f"{name}  grid({row},{col})"
              f"  pos=({tx:6.1f}, {ty:.1f}, {tz:6.1f})"
              f"  rotY={rot_y:6.1f}deg")

si.FlushInstances()
si.Run()
