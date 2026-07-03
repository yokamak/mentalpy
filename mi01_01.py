import mentalpy

# 🧱 [準備] mental ray（レンダラー）を動かすためのインターフェースを立ち上げます
mi = mentalpy.MentalRayInterface()
mi.SetOptions() # 画質や光の計算ルールを自動でセットします

# =========================================================================
# 1. カメラ設定（映画の「ショット」を決める監督の視点！）
# =========================================================================
# pos: カメラの置き場所 [X=0(中央), Y=20(高め), Z=-55(手前に引く)]
# target: カメラが狙いを定める中心ポイント [X=0, Y=5, Z=0]
# filename: 撮影した画像を「mi01_01.tif」という名前で保存します
mi.NewCameraLookAt(name="cam", pos=[0.0, 20.0, -55.0], target=[0.0, 5.0, 0.0], filename="mi01_01.tif")


# =========================================================================
# 2. ライト設定（照明をどこから当てるか？）
# =========================================================================
# pos: 光のスタート地点。左上の奥（X=-50, Y=100, Z=-50）から照らします
# target: 世界の中心 [0, 0, 0] に向かって光を注ぎます
# color: 光の明るさと色。 [0.8, 0.8, 0.8] は少し落ち着いた白い光です
mi.NewLightLookAt(
    name="env_light",
    pos=[-50.0, 100.0, -50.0],
    target=[0.0, 0.0, 0.0],
    color=[0.8, 0.8, 0.8]  # ← 1.0 に近づけると明るく、0.0 に近づけると暗くなります
)


# =========================================================================
# 3. ジオメトリ（形状）の定義 ➔ 【たい焼きの「型」を作るフェーズ】
# =========================================================================
# 💡 ここでは、形や色の「設計図（型紙）」を作るだけで、まだ画面には何も現れません。

# --- 🎨 マテリアル（色や質感の型） ---
mi.NewRedPlasticMaterial("red_plastic", light_inst_name="env_light_inst")

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

# --- 📐 ジオメトリ（形そのものの型） ---
# ①「 sphere_geo 」という名前の、丸い球体の型を用意します
mi.AddBaseSphereObject()

# ②「 ground_geo 」という名前の、平らな地面（四角い板）の型を用意します
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

# ③「 cube_geo 」という名前の、まっすぐな立方体の型を用意します
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
# 4. インスタンス（実体）の生成 ➔ 【型から「たい焼き」を焼き出すフェーズ】
# =========================================================================
# 💡 「型（ジオメトリ）」を再利用して、空間に実体（インスタンス）を生成し、配置します。

# 🟢 地面のインスタンス化
mi.NewInstance("ground_inst", "ground_geo", "white_matte", 
               matrix=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

# 🔴 1つ目のたい焼き：球体の型（sphere_geo）から、実体「 sphere_inst 」を焼き出します！
mi.NewObjectInstance("sphere_inst", "sphere_geo", "red_plastic")
# 📍 この実体だけの「位置・大きさ・回転」を個別に指定します
mi.SetProperty3("sphere_inst", 'translate', -5, 5, 0) # 左に5、上に5の場所へ移動
mi.SetProperty3("sphere_inst", 'scale',     2,  1, 1) # 横幅（X軸）だけ2倍にビヨーンと引き伸ばす（楕円球にする）
mi.SetProperty3("sphere_inst", 'rotate',    0, 0, 90) # Z軸を中心に90度クルッと回転させる

# 🔴 2つ目のたい焼き：立方体の型（cube_geo）から、実体「 cube_inst 」を焼き出します！
mi.NewObjectInstance("cube_inst", 'cube_geo', 'red_plastic')
# 📍 この実体だけの「位置・大きさ・回転」を個別に指定します
mi.SetProperty3("cube_inst", 'translate', 10, 8, 0) # 右に10、上に8の場所へ移動
mi.SetProperty3("cube_inst", 'scale',     1,  1,  1) # 大きさは1倍（元のまま）
mi.SetProperty3("cube_inst", 'rotate',    -30, -20, 0) # X軸に-30度、Y軸に-20度傾けて、カッコいい立体感を出す


# =========================================================================
# ⚙️ 自動翻訳と画像の出力（いざレンダリング！）
# =========================================================================
# FlushInstances: 私たちが指定した個別プロパティを、3ds Maxの実測値に基づいた
#                  mental ray専用の「超難解な逆変換マトリクス（行列）」へ完璧に自動翻訳します。
mi.FlushInstances()

# Run: レンダーコマンドを実行し、mi01_01.tif の画像を出力します！
mi.Run()