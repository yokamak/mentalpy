## はじめに
本ツール mentalpy.py は、3Dグラフィックスの難解な裏側（マトリクス数理）を隠蔽し、Pythonのメソッド形式で直感的にシーンを記述できる「教育用内製ツール」を目指して開発を進めています。

今回のアップデート（中間報告）により、「3Dオブジェクトの3次元構造を汚すことなく、色の情報をインスタンス側から動的に着せ替えるシーングラフ設計（ポリゴン面のマテリアル空文字化）」 が完璧に動作するようになりました。これにより、上記の検証コードの通り、同じひとつの cube_geo というデータから、赤・青・緑のカラーバリエーションの異なる箱をたった数行の直感的なコマンドで横一列に整列させ、その場で美しく自軸回転させる基盤が整いました。

## なぜ今mental rayなのか？
あこがれのmental rayです。海外で活躍されているCG技術の方々が使っていました。ゲームのオープニング映像や映画「マトリックス」など、たくさんの名作で使われてきたプロユースのレンダラーです。当初はSoftimage3Dだけでした。Maya2018,3ds max2018までは使われていました。解説本は2万円以上(Rendering with Mental Rayなど)し、個人としては高価な手に入らないツールでした。
開発の思いは、以下のようなタイトル案にあります。mental rayが持つ「特有の空気感」や「物理的な陰影の美しさ」は独特な魅力があります。
「3Dグラフィックス数学を地続きで学ぶ：PythonとCUIレンダラーによる実践的パイプライン教育の提案」
「3Dグラフィックスの本質（数理やパイプライン）を学ぶ教材として最強！」
「POV-Rayの代わりに使う。Pythonによるシーン記述で3Dシーングラフを基礎から学ぶアカデミックハック」
「数式でハコを並べて色を塗る！高校生から始めるPython 3Dパイプライン開発」
「コードを書いて絵を出す魔法！Pythonであこがれのmental rayを操る3Dグラフィックス入門」

https://qiita.com/yokamak/items/94e6b8c2b2ce941033f3

## 自作パイプライン（mentalpy.py）を使ったシーン記述例

![mi01_02_01.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/4243812/b587a35a-6f6b-4eba-adba-5d8d0938d3cc.jpeg)

```python
import mentalpy

# 🧱 [準備] mental ray（レンダラー）を動かすためのインターフェースを立ち上げます
mi = mentalpy.MentalRayInterface()
mi.SetOptions() # レンダリングの画質や、光の跳ね返り（大域照明）の基本ルールを設定します

# =========================================================================
# 1. カメラ設定（どこからシーンを見るか？）
# =========================================================================
# 【正面カメラ】
# pos: カメラの置き場所 [X=0(中央), Y=25(少し高め), Z=-70(手前に大きく引く)]
# target: カメラがじっと見つめる中心点 [X=0, Y=5, Z=0]
# filename: 撮影した画像を「mi01_02.tif」という名前で保存します
mi.NewCameraLookAt(name="cam", pos=[0.0, 25.0, -70.0], target=[0.0, 5.0, 0.0], filename="mi01_02.tif")

# 【上空カメラ（デバッグ用）】
# 真上から見下ろして位置ズレを確かめたいときは、上の行の先頭に「#」をつけて、下の行の「#」を消します
#mi.NewCameraLookAt(name="cam", pos=[0.0, 70.0, -5.0], target=[0.0, 0.0, 0.0], filename="mi01_02.tif")


# =========================================================================
# 2. ライト設定（太陽や照明の光をどこから当てるか？）
# =========================================================================
# pos: 光のスタート地点。左上の奥（X=-50, Y=100, Z=-50）から照らします
# color: 光の明るさと色。 [0.8, 0.8, 0.8] は少し落ち着いた白い光です（1.0にすると最大になります）
mi.NewLightLookAt(
    name="env_light",
    pos=[-50.0, 100.0, -50.0],
    target=[0.0, 0.0, 0.0],
    color=[0.8, 0.8, 0.8]
)

# =========================================================================
# 3. マテリアル・オブジェクト定義（どんな色や形のパーツを用意するか？）
# =========================================================================

# --- 🎨 色の絵の具（マテリアル）を4種類ブレンドして用意します ---
# ① 定番の「赤プラスチック」
mi.NewRedPlasticMaterial("red_plastic", light_inst_name="env_light_inst")

# ② カスタムで作った「青プラスチック」 (RGBのB(青)を 0.8 と多めに設定)
mi.NewPhongMaterial("blue_plastic", diffuse=[0.2, 0.2, 0.8], ambient=[0.1, 0.1, 0.2])

# ③ カスタムで作った「緑プラスチック」 (RGBのG(緑)を 0.8 と多めに設定)
mi.NewPhongMaterial("green_plastic", diffuse=[0.2, 0.8, 0.2], ambient=[0.1, 0.2, 0.1])

# ④ 特製の「黄金（ゴールド）」 (金属っぽい鋭いツヤを出すために、特別な数値を設定しています)
mi.NewPhongMaterial("gold_metal", diffuse=[0.8, 0.6, 0.1], ambient=[0.2, 0.15, 0.0], specular=[0.5, 0.4, 0.1], exponent=20.0)

# --- 🏢 白い地面の質感を直接テキストで書き込みます ---
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

# クラスに内蔵されている、綺麗な球体（NURBSという数式で描く球）の形を読み込みます
mi.AddBaseSphereObject()

# 📐 平らな「地面の3Dデータ（四角い板）」を定義します
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

# 📦 「立方体（Cube）の3Dデータ（8つの角の座標）」を定義します
# 💡 ポイント：ポリゴンの面（p の行）の色指定をすべて空文字 "" にしています！
# こうすることで、後から「この箱は赤」「この箱は青」とインスタンス側で自由に着せ替えができます。
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
    '        p "" 0 1 5 4\n'  
    '        p "" 1 3 7 5\n'
    '        p "" 3 2 6 7\n'
    '        p "" 2 0 4 6\n'
    '        p "" 4 5 7 6\n'
    '        p "" 2 3 1 0\n'
    '    end group\n'
    'end object\n'
)


# =========================================================================
# 4. 配置（上で作った形に色を塗って、空間に並べよう！）
# =========================================================================

# 地面を世界の中心（マトリクス初期値）にピタッと置きます
mi.NewInstance("ground_inst", "ground_geo", "white_matte", 
               matrix=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

# （球体を使いたい時は、下の4行の「#」を消せば画面の左側に現れます）
#mi.NewObjectInstance("sphere_inst", "sphere_geo", "red_plastic")
#mi.SetProperty3("sphere_inst", 'translate', -5, 5, 0)
#mi.SetProperty3("sphere_inst", 'scale',     2,  1, 1)
#mi.SetProperty3("sphere_inst", 'rotate',    0, 0, 90)

# 🔴 1つ目の箱：中央に置く「赤い立方体」
# translate: [X=0(真ん中), Y=5(地面の上にのせる), Z=0]
mi.NewObjectInstance("cube_inst", 'cube_geo', 'red_plastic')
mi.SetProperty3("cube_inst", 'translate', 0, 5, 0)
mi.SetProperty3("cube_inst", 'scale',     1,  1,  1)
mi.SetProperty3("cube_inst", 'rotate',    0, 0, 0)

# 🔵 2つ目の箱：左側に置く「青い立方体」
# translate: [X=-12(左に12ずらす), Y=5, Z=0]
mi.NewObjectInstance("cube2_inst", 'cube_geo', 'blue_plastic')
mi.SetProperty3("cube2_inst", 'translate', -12, 5, 0)
mi.SetProperty3("cube2_inst", 'scale',     1,  1,  1)
mi.SetProperty3("cube2_inst", 'rotate',    0, 0, 0)

# 🟢 3つ目の箱：右側に置く「緑の立方体」
# translate: [X=12(右に12ずらす), Y=5, Z=0]
mi.NewObjectInstance("cube3_inst", 'cube_geo', 'green_plastic')
mi.SetProperty3("cube3_inst", 'translate', 12, 5, 0)
mi.SetProperty3("cube3_inst", 'scale',     1,  1,  1)
mi.SetProperty3("cube3_inst", 'rotate',    0, 0, 0)

# =========================================================================
# ⚙️ 翻訳とレンダリング（ボタンをプッシュ！）
# =========================================================================
# FlushInstances: 私たちが指定した「位置・大きさ・回転」のバラバラのデータを、
#                  mental rayが理解できる1つの美しい数学行列（4x4トランスフォーム）へ一括自動翻訳します。
mi.FlushInstances()

# Run: 裏側で計算プログラム（ray）を立ち上げ、mi01_02.tif の画像をパッと描き出します！
mi.Run()
```

カメラ、真上から、上空カメラ（デバッグ用）
![mi01_02_02.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/4243812/83a1e7f5-1a4a-48ed-b147-c64f3958e3d6.jpeg)

## 参考資料

https://zenn.dev/yokamak/articles/90d9d6191a72c0

https://zenn.dev/yokamak/articles/7cf5a5ec7fece8

https://zenn.dev/yokamak/scraps/2412e084da9219

https://zenn.dev/yokamak/scraps/402c397d69ec14

https://qiita.com/yokamak/items/6adfda4894e964d8ee0a

https://qiita.com/yokamak/items/6f483172223d39e61f7e

https://qiita.com/yokamak/items/3b11140154e87c264305

## おわりに

まだまだ、検証していかなくてはならないところですが、悪戦苦闘しながら、面白いところです。一歩一歩です。
コンピュータグラフィックスを学ぶうえでのレガシーとなる技術にリスペクトしながら、クリエイティブなパフォーマンスに役立てられたらなと思います。ありがとうございます。
