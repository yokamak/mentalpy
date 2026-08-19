import mentalpy

# 🧱 [準備] 3D空間を描く計算プログラム（mental ray）を動かすための「操作パネル」を立ち上げます
mi = mentalpy.MentalRayInterface()
mi.SetOptions() # 画質や光の計算方法など、レンダリングの基本ルールを自動でセットします

# =========================================================================
# 🌤️ 【追加】Daylight（物理的な太陽・空・カメラフィルター）の定義
# =========================================================================

# ① 物理的な太陽光（mia_physicalsun）の中身を定義します
# direction [-1, -1, -1] で、左・下・手前に向かって光の矢が走り、左手前にかっこいい影が伸びる朝の光を作ります！
sun_light_def = (
    'light "sunShape"\n'
    '    "mia_physicalsun" ( \n'
    '        "on" on, \n'
    '        "multiplier" 1.0,   # 太陽光の強さ（エネルギー）です\n'
    '        "y_is_up" on,       # Y軸を「上空」として扱います\n'
    '        "rgb_unit_conversion" 0.0001 0.0001 0.0001 \n'
    '    )\n'
    '    direction -1. -1. -1.\n'
    'end light\n'
)
mi.commands.append(sun_light_def)

# ② 太陽をシーンに配置するためのスタンド（インスタンス）です。無回転のクリーンな状態で置きます。
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
# 💡 大事なポイント：太陽のスタンド（sunDirection）を、後でステージに並べられるように登録しておきます！
mi.instgroup_members.append("sunDirection")

# ③ 眩しさをちょうどよく引き締めるカメラ用のレンズフィルター（トーンマッピング）です
exposure_shader_def = (
    'shader "mia_exposure_simple1"\n'
    '    "mia_exposure_simple" (\n'
    '        "pedestal" 0.,\n'
    '        "gain" 0.15,         # 画面全体の明るさの調整弁です\n'
    '        "knee" 0.75,\n'
    '        "compression" 3.,\n'
    '        "gamma" 2.2,         # 影を自然に持ち上げるガンマ値です\n'
    '        "use_preview" off\n'
    '    )\n'
)
mi.commands.append(exposure_shader_def)

# ④ 地平線から天頂までのリアルな青空を自動生成する贅沢なシェーダーです
physical_sky_def = (
    'shader "mia_physicalsky1"\n'
    '    "mia_physicalsky" (\n'
    '        "on" on,\n'
    '        "multiplier" 0.5,\n'
    '        "rgb_unit_conversion" 0.0001 0.0001 0.0001 1.,\n'
    '        "haze" 0.,\n'
    '        "redblueshift" -0.4, # 空の青みの調整です\n'
    '        "saturation" 1.,\n'
    '        "horizon_height" -2.5,\n'
    '        "horizon_blur" 0.1,\n'
    '        "ground_color" 0.2 0.2 0.2 1.,\n'
    '        "night_color" 0. 0. 0. 1.,\n'
    '        "sun_direction" 0. 0. 0.,\n'
    '        "sun" "sunDirection",# 【超重要】上で作った太陽のスタンド（sunDirection）とリンクさせます！\n'
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
# 1. カメラ設定（どこから、どこを狙って撮影するか？）
# =========================================================================
# filename: 物理スカイ用の画像として「mi01_00day.tif」という名前で保存します
mi.NewCameraLookAt(name="cam", pos=[0.0, 15.0, -55.0], target=[0.0, 4.0, 0.0], filename="mi01_00day.tif")



# =========================================================================
# 2. ライト設定（今回は上の太陽光がメインになりますが、ベースライトも残します）
# =========================================================================
mi.NewLightLookAt(
    name="env_light",
    pos=[-50.0, 100.0, -50.0],
    target=[0.0, 0.0, 0.0],
    color=[0.8, 0.8, 0.8]
)


# =========================================================================
# 3. マテリアル・オブジェクト定義（どんな色や形のパーツを用意するか？）
# =========================================================================

# --- 🎨 色の絵の具（マテリアル）を定義します ---
mi.NewRedPlasticMaterial("red_plastic", light_inst_name="env_light_inst")

# 白いザラザラした「つや消しの質感（地面用）」
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

# クラス内の球体型紙データを準備
mi.AddBaseSphereObject()

# 📐 平らな「地面の3Dデータ」
ground_geo = (
    'object "ground_geo" visible trace shadow tag 1\n'
    '    group\n'
    '        -50.0  0  -50.0\n'
    '        -50.0  0   50.0\n'
    '         50.0  0  -50.0\n'
    '         50.0  0   50.0\n'
    '        v 0  v 1  v 2  v 3\n'
    '        p "white_matte" 0 1 3 2\n'
    '    end group\n'
    'end object\n'
)
mi.commands.append(ground_geo)

# 📦 「立方体（Cube）の3Dデータ」
mi.commands.append(
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
    '        p "red_plastic" 0 1 5 4\n'
    '        p "red_plastic" 1 3 7 5\n'
    '        p "red_plastic" 3 2 6 7\n'
    '        p "red_plastic" 2 0 4 6\n'
    '        p "red_plastic" 4 5 7 6\n'
    '        p "red_plastic" 2 3 1 0\n'
    '    end group\n'
    'end object\n'
)


# =========================================================================
# 4. 配置（上で作った形を、空間内の指定した場所に並べよう！）
# =========================================================================

# 地面を世界の中心にピタッと置きます
mi.NewInstance("ground_inst", "ground_geo", "white_matte", 
               matrix=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

# 立方体を空間に配置します
mi.NewObjectInstance("cube_inst", 'cube_geo', 'red_plastic')
mi.SetProperty3("cube_inst", 'translate', 0, 5, 0)
mi.SetProperty3("cube_inst", 'scale',     1,  1,  1)
mi.SetProperty3("cube_inst", 'rotate',    0, 0, 0)


# =========================================================================
# ⚙️ レンズフィルターとスカイ背景をカメラにカチッとドッキング！
# =========================================================================
# 💡 ここが魔法の部分です！
# ツールが自動生成した通常のカメラのテキストデータを探し出して、
# 『レンズフィルター（lens）』と『青空背景（environment）』を強制追記してカメラをパワーアップさせます！
for idx, cmd in enumerate(mi.commands):
    if 'camera "cam"' in cmd:
        upgraded_camera = cmd.replace(
            'end camera',
            '    lens = "mia_exposure_simple1"\n    environment = "mia_physicalsky1"\nend camera'
        )
        mi.commands[idx] = upgraded_camera

# 私たちが指定した「位置」などのデータをレンダラー用の4x4マトリクス行列へ一括翻訳します
mi.FlushInstances()

# 裏側で計算プログラム（ray）を叩き起こし、青空が広がる美しい画像（mi01_00day.tif）を描き出します！
mi.Run()