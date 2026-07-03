import subprocess
import sys
import math

class MentalRayInterface:
    def __init__(self):
        self.commands = []
        self.instgroup_members = []
        self.instance_transforms = {}
        self.commands.append('verbose off\nlink "base.so"\n$include <base.mi>\n')

    def SetOptions(self, samples_min=-1, samples_max=2):
        options = (
            f'options "opt"\n'
            f'    samples      {samples_min} {samples_max}\n'
            f'    contrast     .1 .1 .1 .1\n'
            f'    trace depth  2 2\n'
            f'    globillum    on\n'
            f'    finalgather  on\n'
            f'end options\n'
        )
        self.commands.append(options)

    def _compute_lookat_matrix(self, pos, target, roll=0.0, scale=1.0):
        f_x = pos[0] - target[0]
        f_y = pos[1] - target[1]
        f_z = pos[2] - target[2]
        len_f = math.sqrt(f_x**2 + f_y**2 + f_z**2)
        if len_f == 0: len_f = 1.0
        f_x, f_y, f_z = f_x / len_f, f_y / len_f, f_z / len_f
        up_x, up_y, up_z = 0.0, 1.0, 0.0
        if abs(f_x) < 0.0001 and abs(f_z) < 0.0001:
            up_x, up_y, up_z = 0.0, 0.0, 1.0 if f_y > 0 else -1.0
        r_x = up_y * f_z - up_z * f_y
        r_y = up_z * f_x - up_x * f_z
        r_z = up_x * f_y - up_y * f_x
        len_r = math.sqrt(r_x**2 + r_y**2 + r_z**2)
        if len_r == 0: len_r = 1.0
        r_x, r_y, r_z = r_x / len_r, r_y / len_r, r_z / len_r
        u_x = f_y * r_z - f_z * r_y
        u_y = f_z * r_x - f_x * r_z
        u_z = f_x * r_y - f_y * r_x
        rot_y = math.asin(r_z)
        if abs(math.cos(rot_y)) > 0.0001:
            rot_x = math.atan2(-u_z, f_z)
            rot_z = math.atan2(-r_y, r_x)
        else:
            rot_x = math.atan2(f_y, u_y)
            rot_z = 0.0
        rot_z += math.radians(roll)
        cx, sx = math.cos(rot_x), math.sin(rot_x)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        cz, sz = math.cos(rot_z), math.sin(rot_z)
        m00, m01, m02 = cz * cy, sz * cx + cz * sy * sx, sz * sx - cz * sy * cx
        m10, m11, m12 = -sz * cy, cz * cx - sz * sy * sx, cz * sx + sz * sy * cx
        m20, m21, m22 = sy, -cy * sx, cy * cx
        s = 1.0 / scale if scale != 0 else 1.0
        m00, m01, m02 = m00 * s, m01 * s, m02 * s
        m10, m11, m12 = m10 * s, m11 * s, m12 * s
        m20, m21, m22 = m20 * s, m21 * s, m22 * s
        tx, ty, tz = -pos[0], -pos[1], -pos[2]
        final_tx = tx * m00 + ty * m10 + tz * m20
        final_ty = tx * m01 + ty * m11 + tz * m21
        final_tz = tx * m02 + ty * m12 + tz * m22
        return [[m00, m01, m02], [m10, m11, m12], [m20, m21, m22], [final_tx, final_ty, final_tz]]

    def NewCameraLookAt(self, name, pos, target, roll=0.0, scale=1.0, filename="out.tif", res_x=640, res_y=480):
        mat = self._compute_lookat_matrix(pos, target, roll, scale)
        camera = f'camera "{name}"\n    output "rgba" "{filename}"\n    focal 50.0\n    aperture 36.0\n    aspect 1.33333\n    resolution {res_x} {res_y}\nend camera\n'
        self.commands.append(camera)
        cam_inst = f'instance "{name}_inst" "{name}"\n    transform       {mat[0][0]:.4f} {mat[0][1]:.4f} {mat[0][2]:.4f} 0.0\n                    {mat[1][0]:.4f} {mat[1][1]:.4f} {mat[1][2]:.4f} 0.0\n                    {mat[2][0]:.4f} {mat[2][1]:.4f} {mat[2][2]:.4f} 0.0\n                    {mat[3][0]:.4f} {mat[3][1]:.4f} {mat[3][2]:.4f} 1.0\nend instance\n'
        self.commands.append(cam_inst)
        self.instgroup_members.append(f"{name}_inst")

    def NewLightLookAt(self, name, pos, target, roll=0.0, scale=1.0, color=[1.0, 1.0, 1.0]):
        mat = self._compute_lookat_matrix(pos, target, roll, scale)
        light_def = f'light "{name}"\n    "mib_light_infinite" (\n        "color" {color[0]} {color[1]} {color[2]},\n        "shadow" on\n    )\nend light\n'
        self.commands.append(light_def)
        light_inst = f'instance "{name}_inst" "{name}"\n    transform       {mat[0][0]:.4f} {mat[0][1]:.4f} {mat[0][2]:.4f} 0.0\n                    {mat[1][0]:.4f} {mat[1][1]:.4f} {mat[1][2]:.4f} 0.0\n                    {mat[2][0]:.4f} {mat[2][1]:.4f} {mat[2][2]:.4f} 0.0\n                    {mat[3][0]:.4f} {mat[3][1]:.4f} {mat[3][2]:.4f} 1.0\nend instance\n'
        self.commands.append(light_inst)
        self.instgroup_members.append(f"{name}_inst")

    def NewRedPlasticMaterial(self, name, light_inst_name="env_light_inst"):
        material = f'material "{name}"\n    "mib_illum_phong" (\n        "ambient" 0.2 0.1 0.1,\n        "diffuse" 0.8 0.2 0.2,\n        "specular" 0.9 0.9 0.9,\n        "exponent" 50.0,\n        "lights" ["{light_inst_name}"]\n    )\nend material\n'
        self.commands.append(material)
    
    def NewPhongMaterial(self, name, diffuse=[0.8, 0.2, 0.2], ambient=[0.2, 0.1, 0.1], specular=[0.9, 0.9, 0.9], exponent=50.0, light_inst_name="env_light_inst"):
        """
        RGBを自由に変えられる汎用Phongマテリアル関数
        diffuse, ambient, specular に [R, G, B] の配列を渡します。
        """
        material = (
            f'material "{name}"\n'
            f'    "mib_illum_phong" (\n'
            f'        "ambient" {ambient[0]} {ambient[1]} {ambient[2]},\n'
            f'        "diffuse" {diffuse[0]} {diffuse[1]} {diffuse[2]},\n'
            f'        "specular" {specular[0]} {specular[1]} {specular[2]},\n'
            f'        "exponent" {exponent},\n'
            f'        "lights" ["{light_inst_name}"]\n'
            f'    )\n'
            f'end material\n'
        )
        self.commands.append(material)
        

    def NewMiaMaterialX(self, name, diffuse=[0.5, 0.5, 0.5], reflectivity=0.6, roughness=0.0, glossiness=1.0, ior=1.4, transparency=0.0, light_inst_name="env_light_inst"):
        """
        mental ray の最高峰万能シェーダー mia_material_x を定義する汎用関数
        """
        material = (
            f'material "{name}"\n'
            f'    "mia_material_x" (\n'
            f'        "diffuse" {diffuse[0]} {diffuse[1]} {diffuse[2]},\n'
            f'        "reflectivity" {reflectivity},\n'
            f'        "refl_roughness" {roughness},\n'
            f'        "refl_gloss" {glossiness},\n'
            f'        "ior" {ior},\n'
            f'        "refr_transparency" {transparency},\n'
            f'        "lights" ["{light_inst_name}"]\n'
            f'    )\n'
            f'end material\n'
        )
        self.commands.append(material)
        

    def AddBaseSphereObject(self):
        sphere_geo = (
            'object "sphere_geo" visible shadow trace tag 1\n'
            '    basis "bs" bspline 3\n'
            '    group\n'
            '             0.0000  5.0000  0.0000          0.7957  5.0000  1.3781\n'
            '            -0.7956  5.0000  1.3781         -1.5913  5.0000  0.0000\n'
            '            -0.7957  5.0000 -1.3781          0.7956  5.0000 -1.3781\n'
            '             1.5913  5.0000  0.0000          2.3448  3.9181  4.0613\n'
            '            -2.3448  3.9181  4.0613         -4.6896  3.9181  0.0000\n'
            '            -2.3448  3.9181 -4.0613          2.3448  3.9181 -4.0613\n'
            '             4.6896  3.9181  0.0000          3.3276  0.0000  5.7636\n'
            '            -3.3276  0.0000  5.7636         -6.6552  0.0000  0.0000\n'
            '            -3.3276  0.0000 -5.7636          3.3276  0.0000 -5.7636\n'
            '             6.6552  0.0000  0.0000          2.3448 -3.9181  4.0613\n'
            '            -2.3448 -3.9181  4.0613         -4.6896 -3.9181  0.0000\n'
            '            -2.3448 -3.9181 -4.0613          2.3448 -3.9181 -4.0613\n'
            '             4.6896 -3.9181  0.0000          0.7957 -5.0000  1.3781\n'
            '            -0.7956 -5.0000  1.3781         -1.5913 -5.0000  0.0000\n'
            '            -0.7957 -5.0000 -1.3781          0.7956 -5.0000 -1.3781\n'
            '             1.5913 -5.0000  0.0000          0.0000 -5.0000  0.0000\n'
            '\n'
            '            v 0     v 1     v 2     v 3     v 4     v 5     v 6     v 7\n'
            '            v 8     v 9     v 10    v 11    v 12    v 13    v 14    v 15\n'
            '            v 16    v 17    v 18    v 19    v 20    v 21    v 22    v 23\n'
            '            v 24    v 25    v 26    v 27    v 28    v 29    v 30    v 31\n'
            '\n'
            '            surface "surf" ""\n'
            '                    "bs" 0 6   -3. -2. -1. 0. 1. 2. 3. 4. 5. 6. 7. 8. 9.\n'
            '                    "bs" 0 4    0.  0.  0. 0. 1. 2. 3. 4. 4. 4. 4.\n'
            '\n'
            '                    31 31 31 31 31 31 31 31 31 26 25 30 29 28 27 26\n'
            '                    25 30 20 19 24 23 22 21 20 19 24 14 13 18 17 16\n'
            '                    15 14 13 18  8  7 12 11 10  9  8  7 12  2  1  6\n'
            '                     5  4  3  2  1  6  0  0  0  0  0  0  0  0  0\n'
            '\n'
            '            approximate surface parametric 3 3 "surf"\n'
            '    end group\n'
            'end object\n'
        )
        self.commands.append(sphere_geo)

    def NewObjectInstance(self, inst_name, obj_name, material_name):
        self.instance_transforms[inst_name] = {
            'obj_name': obj_name,
            'material_name': material_name,
            'translate': [0.0, 0.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': [1.0, 1.0, 1.0],
            'transform_order': 'ORDER_SRT',
            'rotate_order': 'ORDER_XYZ'
        }
        self.instgroup_members.append(inst_name)

    def SetProperty3(self, inst_name, prop_name, v0, v1, v2):
        if inst_name in self.instance_transforms:
            if prop_name in ['translate', 'rotate', 'scale']:
                self.instance_transforms[inst_name][prop_name] = [float(v0), float(v1), float(v2)]

    def _matmul_4x4(self, A, B):
        """ 4x4 2次元配列の行列乗算 """
        C = [[0.0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                C[i][j] = A[i][0]*B[0][j] + A[i][1]*B[1][j] + A[i][2]*B[2][j] + A[i][3]*B[3][j]
        return C

    # =========================================================================
    # 🔴 NumPy の絶対正解アルゴリズムを素のPythonで100%再現
    # =========================================================================
    def _build_fujiyama_matrix(self, props):
        tx, ty, tz = props['translate'][0], props['translate'][1], props['translate'][2]
        rx, ry, rz = props['rotate'][0], props['rotate'][1], props['rotate'][2]
        sx, sy, sz = props['scale'][0], props['scale'][1], props['scale'][2]

        # 1. 各個別マトリクスの定義 (提示コードと完全一致)
        inv_sx = 1.0 / sx if sx != 0 else 1.0
        inv_sy = 1.0 / sy if sy != 0 else 1.0
        inv_sz = 1.0 / sz if sz != 0 else 1.0
        scale_mat = [
            [inv_sx, 0.0, 0.0, 0.0],
            [0.0, inv_sy, 0.0, 0.0],
            [0.0, 0.0, inv_sz, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

        rad_x, rad_y, rad_z = math.radians(rx), math.radians(ry), math.radians(rz)
        cx, sx_r = math.cos(rad_x), math.sin(rad_x)
        cy, sy_r = math.cos(rad_y), math.sin(rad_y)
        cz, sz_r = math.cos(rad_z), math.sin(rad_z)

        rot_x = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, cx, sx_r, 0.0],
            [0.0, -sx_r, cx, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        rot_y = [
            [cy, 0.0, -sy_r, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [sy_r, 0.0, cy, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        rot_z = [
            [cz, sz_r, 0.0, 0.0],
            [-sz_r, cz, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

        # 2. 回転を結合 np.matmul(rotation_x, np.matmul(rotation_y, rotation_z))
        combined_rot = self._matmul_4x4(rot_y, rot_z)
        combined_rot = self._matmul_4x4(rot_x, combined_rot)

        # 3. トランスフォーム基本行列の合成 np.matmul(scale, combined_rotation)
        transform = self._matmul_4x4(scale_mat, combined_rot)

        # 4. 翻訳ベクトルに適用 transformed_translation = np.matmul(transform, [-tx, -ty, -tz, 1])
        t_vec = [-tx, -ty, -tz, 1.0]
        trans_t = [0.0] * 4
        for i in range(4):
            trans_t[i] = transform[i][0]*t_vec[0] + transform[i][1]*t_vec[1] + transform[i][2]*t_vec[2] + transform[i][3]*t_vec[3]

        # 5. 最終的な転置前の行列を構築
        result = [row[:] for row in transform]
        result[0][3] = trans_t[0]
        result[1][3] = trans_t[1]
        result[2][3] = trans_t[2]

        # 6. 転置して1次元フラットにして返却 (.T)
        flat_matrix = []
        for j in range(4):
            for i in range(4):
                flat_matrix.append(result[i][j])
        return flat_matrix

    def FlushInstances(self):
        for inst_name, props in self.instance_transforms.items():
            mat = self._build_fujiyama_matrix(props)
            inst_cmd = (
                f'instance "{inst_name}" "{props["obj_name"]}"\n'
                f'    material "{props["material_name"]}"\n'
                f'    transform       {mat[0]:.4f} {mat[1]:.4f} {mat[2]:.4f} {mat[3]:.4f}\n'
                f'                    {mat[4]:.4f} {mat[5]:.4f} {mat[6]:.4f} {mat[7]:.4f}\n'
                f'                    {mat[8]:.4f} {mat[9]:.4f} {mat[10]:.4f} {mat[11]:.4f}\n'
                f'                    {mat[12]:.4f} {mat[13]:.4f} {mat[14]:.4f} {mat[15]:.4f}\n'
                f'end instance\n'
            )
            self.commands.append(inst_cmd)

    def NewInstance(self, inst_name, obj_name, material_name, matrix=None):
        if matrix is None:
            matrix = [1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1]
        m = matrix
        inst = (
            f'instance "{inst_name}" "{obj_name}"\n'
            f'    material "{material_name}"\n'
            f'    transform       {m[0]} {m[1]} {m[2]} {m[3]}\n'
            f'                    {m[4]} {m[5]} {m[6]} {m[7]}\n'
            f'                    {m[8]} {m[9]} {m[10]} {m[11]}\n'
            f'                    {m[12]} {m[13]} {m[14]} {m[15]}\n'
            f'end instance\n'
        )
        self.commands.append(inst)
        self.instgroup_members.append(inst_name)

    def Run(self, camera_name="cam", options="opt"):
        group = 'instgroup "scene"\n'
        for member in self.instgroup_members:
            group += f'    "{member}"\n'
        group += 'end instgroup\n'
        self.commands.append(group)
        self.commands.append(f'render "scene" "{camera_name}_inst" "{options}"\n')
        full_mi_script = "\n".join(self.commands)
        print(full_mi_script)
        try:
            p = subprocess.Popen('ray', shell=False, stdin=subprocess.PIPE, text=True)
            p.communicate(full_mi_script)
        except OSError as e:
            print(f"error: mental ray execution failed: {e}")