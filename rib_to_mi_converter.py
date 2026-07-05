#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rib_to_mi_converter.py

Convert RenderMan RIB bicubic Bezier patches to mental ray
free-form surfaces (.mi scene format).

This tool extracts Patch "bicubic" statements from a RIB file
(e.g. exported by sPatch or HamaPatch) and generates a model-only
.mi file containing degree-3 Bezier surfaces, ready to be included
in a mental ray scene via $include. Control points are passed
through unmodified: both RIB and .mi use a Y-up right-handed
coordinate system, so no axis conversion is required.

Features:
  - One RIB bicubic patch -> one mental ray "surface" statement
    (basis "bezier 3", parametric approximation)
  - Adjustable tessellation via approx_factor
    (subdivisions per patch = factor x degree)
  - Optional "tagged" mode: surfaces carry label 0 instead of a
    material name, so the material can be assigned per-instance
    (verified with mental ray 3.14 standalone)
  - Optional u/v transposition of the control point grid

Usage:
    python rib_to_mi_converter.py input.rib [output.mi]

    The object name is derived from the output file name
    (or the input file name if no output is given).

Part of the mentalpy toolset:
    https://github.com/yokamak/mentalpy

Tested with mental ray 3.14 standalone.

------------------------------------------------------------------
MIT License

Copyright (c) 2026 Yuichirou Yokomakura

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------------------------------------------
"""

import re
import sys


def parse_rib_patches(rib_content):
    """RIBファイルからbicubic patchデータを解析する"""
    patches = []

    # 括弧内を非貪欲で取得（複数行のpatchにも対応）
    patch_pattern = r'Patch\s+"bicubic"\s+"P"\s+\[(.*?)\]'
    matches = re.findall(patch_pattern, rib_content, re.DOTALL)

    # 指数表記（1e-05等）にも対応した数値パターン
    num_pattern = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'

    for i, match in enumerate(matches):
        points = [float(n) for n in re.findall(num_pattern, match)]
        if len(points) == 48:
            patches.append(points)
        else:
            print(f"警告: パッチ{i + 1}に{len(points)}個の値があります"
                  f"（期待値: 48）-- スキップします")

    return patches


def convert_patches_to_mi(patches, object_name="model", material_name="default_mtl",
                          approx_factor=2.0, transpose_uv=False, tagged=True):
    """
    RIB bicubic patch群を mental ray の free-form surface (.mi) に変換

    Parameters:
    - object_name:   .mi 内の object 名
    - material_name: surface が参照する material 名（メインシーン側で定義しておく）
                     tagged=True の場合は無視される
    - approx_factor: approximate surface parametric の係数
                     (分割数 = factor × degree3。2.0でパッチあたり6分割)
    - transpose_uv:  制御点グリッドの u/v を転置する場合 True
    - tagged:        True の場合、object に tagged フラグを立て、
                     surface はマテリアル名の代わりにラベル0を持つ。
                     マテリアルは instance 側の material 指定で解決される
    """
    if not tagged and not material_name:
        print('警告: material_nameが空です。"default_mtl"を使用します')
        material_name = "default_mtl"

    lines = []
    lines.append(f'object "{object_name}"')
    lines.append('    visible on')
    lines.append('    shadow on')
    lines.append('    trace on')
    if tagged:
        lines.append('    tagged on')
    lines.append('    basis "bez3" bezier 3')
    lines.append('    group')

    # --- vector list: 全パッチの制御点を連結 ---
    lines.append('        # vectors (control points)')
    for pi, patch in enumerate(patches):
        lines.append(f'        # patch {pi + 1}')
        for j in range(16):
            x, y, z = patch[3 * j], patch[3 * j + 1], patch[3 * j + 2]
            lines.append(f'        {x:.6f} {y:.6f} {z:.6f}')

    # --- vertex list: vectorを単純に1:1参照 ---
    lines.append('        # vertices')
    for i in range(len(patches) * 16):
        lines.append(f'        v {i}')

    # --- surface list: 1パッチ = 1 surface ---
    lines.append('        # surfaces')
    surf_names = []
    for pi in range(len(patches)):
        base = pi * 16
        name = f'{object_name}_s{pi + 1:03d}'
        surf_names.append(name)

        order = list(range(16))
        if transpose_uv:
            order = [4 * (k % 4) + k // 4 for k in range(16)]
        idx_str = ' '.join(str(base + k) for k in order)

        if tagged:
            lines.append(f'        surface "{name}" 0')
        else:
            lines.append(f'        surface "{name}" "{material_name}"')
        lines.append('            "bez3" 0.0 1.0  0.0 1.0')  # u: range 0..1, params 0 1
        lines.append('            "bez3" 0.0 1.0  0.0 1.0')  # v: range 0..1, params 0 1
        lines.append(f'            {idx_str}')

    # --- approximation ---
    for name in surf_names:
        lines.append(f'        approximate surface parametric '
                     f'{approx_factor} {approx_factor} "{name}"')

    lines.append('    end group')
    lines.append('end object')
    return '\n'.join(lines)


def rib_to_mi_converter(rib_file_path, output_file_path=None,
                        object_name="model", material_name="default_mtl",
                        approx_factor=2.0, transpose_uv=False, tagged=True):
    """RIBファイルを model-only の .mi に変換"""
    try:
        with open(rib_file_path, 'r') as f:
            rib_content = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイル '{rib_file_path}' が見つかりません")
        return None

    patches = parse_rib_patches(rib_content)
    if not patches:
        print("パッチデータが見つかりませんでした")
        return None
    print(f"{len(patches)}個のパッチが見つかりました")

    if output_file_path is None:
        output_file_path = rib_file_path.replace('.rib', '_model.mi')

    mtl_note = ('instance側の material 指定で解決 (tagged)' if tagged
                else f'material "{material_name}" をメインシーンで先に宣言')
    header = f"""# model-only mi file converted from {rib_file_path}
# material: {mtl_note}
# usage (in main scene):
#
#   $include "{output_file_path}"
#
#   instance "{object_name}_inst" "{object_name}"
#       material "your_material"
#       # transform <world-to-object 4x4 matrix here>
#   end instance
#
#   ... add "{object_name}_inst" to your instgroup

"""
    with open(output_file_path, 'w') as f:
        f.write(header)
        f.write(convert_patches_to_mi(patches, object_name, material_name,
                                      approx_factor, transpose_uv, tagged))
        f.write('\n')

    print(f"変換完了: {output_file_path}")
    print(f"総surface数: {len(patches)}")
    return output_file_path


def preview_conversion(rib_content, num_patches=3):
    """変換結果のプレビューを表示"""
    patches = parse_rib_patches(rib_content)
    if not patches:
        print("パッチデータが見つかりませんでした")
        return

    n = min(num_patches, len(patches))
    print(f"\n=== 変換プレビュー（最初の{n}パッチ） ===")
    print(convert_patches_to_mi(patches[:n]))  # 戻り値は文字列


# メイン実行部分
import os

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # コマンドライン: python rib_to_mi_converter.py input.rib [output.mi]
        out = sys.argv[2] if len(sys.argv) >= 3 else None

        # object名の決定: 出力ファイル名（なければ入力ファイル名）のベース部分
        name_source = out if out else sys.argv[1]
        obj_name = os.path.splitext(os.path.basename(name_source))[0]

        rib_to_mi_converter(sys.argv[1], out, object_name=obj_name)
    else:
        print("=== RIB to mental ray (.mi) Converter ===")
        print("使い方: python rib_to_mi_converter.py input.rib [output.mi]\n")

        sample_rib = '''Patch "bicubic" "P" [0.500000 1.062500 0.000000 0.500000 1.062500 -0.114805 0.434733 1.062500 -0.272374 0.353554 1.062500 -0.353553 0.429688 1.006250 0.000000 0.429688 1.006250 -0.114805 0.385015 1.006250 -0.222655 0.303835 1.006250 -0.303835 0.307276 0.954832 0.000000 0.307276 0.954832 -0.060990 0.260404 0.954832 -0.174150 0.217277 0.954832 -0.217277 0.265625 0.875000 0.000000 0.265625 0.875000 -0.060990 0.230952 0.875000 -0.144698 0.187825 0.875000 -0.187825 ]'''
        preview_conversion(sample_rib, 1)