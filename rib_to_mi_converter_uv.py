#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rib_to_mi_converter_uv.py — RIB bicubic patch → mental ray .mi 変換(UV付き)

元の rib_to_mi_converter_.py に、MDL マテリアル対応のための UV 機能を追加:

  uv_mode:
    "parametric"  : 暗黙のパラメータ座標のみ(各パッチ 0..1、柄はパッチごとに繰り返す)
                    → bad texture 回避だけならこれで十分なはず
    "cylindrical" : 各パッチ4隅の制御点を円筒投影してグローバル UV を計算し、
                    線形 texture surface として付与(回転体で木目が連続する)

texture surface 構文は 3.14 standalone 実機で検証済み:
  - texture のパラメータリストは「基底名 + パラメータ列」のみ(範囲指定なし)
  - 範囲を書くと GEOC 091008 "Parameters not strictly increasing" で失敗する
  - MDL バンプ付きマテリアルにはテクスチャ座標が必須(ポリゴンは t 頂点、
    自由曲面は texture surface)。欠落時は bad texture エラー +
    FG ポイント汚染による正方形ノイズが発生する。
"""

import math
import re


def parse_rib_patches(rib_content):
    """RIB から Patch "bicubic" の制御点 16 点 ×3 座標を抽出"""
    patches = []
    patch_pattern = r'Patch\s+"bicubic"\s+"P"\s+\[([\d\s\.\-eE]+)\]'
    for match in re.findall(patch_pattern, rib_content):
        points = [float(n) for n in re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', match)]
        if len(points) == 48:
            patches.append(points)
        else:
            print(f'警告: パッチに{len(points)}個の値(期待値48)、スキップ')
    return patches


# ---------------------------------------------------------------- UV 計算

def _corner_points(patch):
    """4x4 制御点グリッドの4隅 (u0v0, u1v0, u0v1, u1v1) を返す。
    RIB の Patch "P" は u が先に変化する行優先。"""
    def pt(i):
        return (patch[3*i], patch[3*i+1], patch[3*i+2])
    return [pt(0), pt(3), pt(12), pt(15)]


def cylindrical_corner_uvs(patches):
    """全パッチの4隅にグローバル円筒 UV を割り当てる。
    u: Y軸まわりの角度(0..1)、v: 高さの正規化(0..1)。
    継ぎ目(u の 1→0 折り返し)はパッチ内で展開して連続化する。"""
    ys = [p[3*i+1] for p in patches for i in range(16)]
    ymin, ymax = min(ys), max(ys)
    yrange = (ymax - ymin) or 1.0

    all_uvs = []
    for patch in patches:
        uvs = []
        for (x, y, z) in _corner_points(patch):
            u = math.atan2(x, z) / (2.0 * math.pi) + 0.5
            v = (y - ymin) / yrange
            uvs.append([u, v])
        # 継ぎ目の展開: パッチが経線をまたぐ場合、小さい側の u に +1
        us = [uv[0] for uv in uvs]
        if max(us) - min(us) > 0.5:
            for uv in uvs:
                if uv[0] < 0.5:
                    uv[0] += 1.0
        # 軸上の点 (x=z=0) は atan2 が不定なので隣の値に合わせる
        for k, (x, y, z) in enumerate(_corner_points(patch)):
            if abs(x) < 1e-9 and abs(z) < 1e-9:
                others = [uvs[m][0] for m in range(4) if m != k]
                uvs[k][0] = sum(others) / len(others)
        all_uvs.append(uvs)
    return all_uvs


# ---------------------------------------------------------------- .mi 出力

def convert_patches_to_mi(patches, object_name='vase', material_name='',
                          approx_factor=4.0, transpose_uv=False,
                          uv_mode='cylindrical'):
    lines = []
    lines.append(f'object "{object_name}"')
    lines.append('    visible on')
    lines.append('    shadow on')
    lines.append('    trace on')
    lines.append('    basis "bez3" bezier 3')
    if uv_mode == 'cylindrical':
        lines.append('    basis "bez1" bezier 1')
    lines.append('    group')

    n_geo_vec = len(patches) * 16

    # --- vector list: 幾何制御点 ---
    lines.append('        # vectors (geometry control points)')
    for pi, patch in enumerate(patches):
        lines.append(f'        # patch {pi + 1}')
        for j in range(16):
            x, y, z = patch[3*j], patch[3*j+1], patch[3*j+2]
            lines.append(f'        {x:.6f} {y:.6f} {z:.6f}')

    # --- vector list: テクスチャ制御点(u, v, 0) ---
    corner_uvs = None
    if uv_mode == 'cylindrical':
        corner_uvs = cylindrical_corner_uvs(patches)
        lines.append('        # vectors (texture control points: u v 0)')
        for pi, uvs in enumerate(corner_uvs):
            for (u, v) in uvs:
                lines.append(f'        {u:.6f} {v:.6f} 0.000000')

    # --- vertex list ---
    n_tex_vec = len(patches) * 4 if uv_mode == 'cylindrical' else 0
    lines.append('        # vertices')
    for i in range(n_geo_vec + n_tex_vec):
        lines.append(f'        v {i}')

    # --- surfaces ---
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

        lines.append(f'        surface "{name}" "{material_name}"')
        lines.append('            "bez3" 0.0 1.0  0.0 1.0')
        lines.append('            "bez3" 0.0 1.0  0.0 1.0')
        lines.append(f'            {idx_str}')

        if uv_mode == 'cylindrical':
            # 線形 texture surface: 4隅のテクスチャ制御点を参照
            # 注意: texture のパラメータリストは「基底名 + パラメータ列」のみ。
            # 幾何側のような範囲(min max)を書くと
            # "Parameters not strictly increasing" でパースに失敗する(3.14 実機で確認済み)。
            # パラメータ列 0.0 1.0 は幾何 surface のパラメータ域(0..1)全体を
            # 1 セグメントでカバーする意味。
            tbase = n_geo_vec + pi * 4
            lines.append('            texture "bez1" 0.0 1.0')
            lines.append('                    "bez1" 0.0 1.0')
            lines.append(f'                    {tbase} {tbase+1} {tbase+2} {tbase+3}')

    # --- approximation ---
    for name in surf_names:
        lines.append(f'        approximate surface parametric '
                     f'{approx_factor} {approx_factor} "{name}"')

    lines.append('    end group')
    lines.append('end object')
    return '\n'.join(lines)


def rib_to_mi_converter(rib_file_path, output_file_path=None,
                        object_name='vase', material_name='',
                        approx_factor=4.0, transpose_uv=False,
                        uv_mode='cylindrical'):
    with open(rib_file_path, 'r') as f:
        rib_content = f.read()

    patches = parse_rib_patches(rib_content)
    print(f'{len(patches)}個のパッチが見つかりました')
    if not patches:
        return

    if output_file_path is None:
        output_file_path = rib_file_path.replace('.rib', '_model.mi')

    header = f"""# model-only mi file converted from {rib_file_path}
# uv_mode = {uv_mode}
#   parametric  : texture surface なし。MDL のバンプ付きマテリアルでは
#                 mi_lookup_vector_texture: bad texture が出る(3.14 実機で確認済み)。
#                 テクスチャ不要のマテリアル専用。
#   cylindrical : 円筒投影のグローバル UV を texture surface として付与。
#                 MDL マテリアルを使う場合はこちら必須。
"""
    with open(output_file_path, 'w') as f:
        f.write(header)
        f.write(convert_patches_to_mi(patches, object_name, material_name,
                                      approx_factor, transpose_uv, uv_mode))
        f.write('\n')

    print(f'変換完了: {output_file_path} (uv_mode={uv_mode})')


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='RIB bicubic → .mi 変換(UV付き)')
    ap.add_argument('rib_file')
    ap.add_argument('-o', '--output')
    ap.add_argument('--name', default='vase')
    ap.add_argument('--material', default='')
    ap.add_argument('--approx', type=float, default=4.0)
    ap.add_argument('--transpose-uv', action='store_true')
    ap.add_argument('--uv', choices=['parametric', 'cylindrical'],
                    default='cylindrical')
    args = ap.parse_args()
    rib_to_mi_converter(args.rib_file, args.output, args.name,
                        args.material, args.approx, args.transpose_uv,
                        uv_mode=args.uv)
