import bpy
import math
import random
import os


# --------------------------------------------------
# CONFIGURACIÓN BASE
# --------------------------------------------------

base_output_folder = r"\datos" #CAMBIAR ESTA RUTA!!

scene_names = ["escena3_1", "escena3_2", "escena3_3"]

NUM_OBJECTS = 12
SEED_BASE   = 42

distance = 25.0


# --------------------------------------------------
# MATERIAL BLANCO
# --------------------------------------------------
def get_white_material():
    name = "White"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value  = 0.6
    return mat


OBJECT_TYPES = [
    "CUBE",
    "CYLINDER",
    "RECT_PRISM",
    "SPHERE",
    "CONE",
    "TORUS",
    "MONKEY",
]

def add_random_object(mat, pos_range=6.0, scale_min=0.4, scale_max=1.5):
    obj_type = random.choice(OBJECT_TYPES)
    s  = random.uniform(scale_min, scale_max)
    px = random.uniform(-pos_range, pos_range)
    py = random.uniform(-pos_range, pos_range)

    if obj_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, s * 0.5))
        obj = bpy.context.object
        obj.scale = (s, s, s)

    elif obj_type == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0,
                                             location=(px, py, s * 0.5))
        obj = bpy.context.object
        obj.scale = (s, s, s)

    elif obj_type == "RECT_PRISM":
        sx = random.uniform(0.5, 1.8)
        sy = random.uniform(0.5, 1.8)
        sz = s
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, sz * 0.5))
        obj = bpy.context.object
        obj.scale = (sx, sy, sz)

    elif obj_type == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(px, py, s * 0.5))
        obj = bpy.context.object
        obj.scale = (s, s, s)

    elif obj_type == "CONE":
        bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1.0,
                                         location=(px, py, s * 0.5))
        obj = bpy.context.object
        obj.scale = (s, s, s)

    elif obj_type == "TORUS":
        major_r = 0.4 * s
        minor_r = 0.15 * s
        bpy.ops.mesh.primitive_torus_add(major_radius=major_r,
                                          minor_radius=minor_r,
                                          location=(px, py, minor_r + 0.05))
        obj = bpy.context.object

    elif obj_type == "MONKEY":
        bpy.ops.mesh.primitive_monkey_add(size=s, location=(px, py, s * 0.5))
        obj = bpy.context.object

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    if obj_type in ("SPHERE", "CONE", "TORUS", "MONKEY"):
        bpy.ops.object.shade_smooth()

    return obj


# --------------------------------------------------
# FUNCIÓN PRINCIPAL: RENDERIZAR UNA ESCENA
# --------------------------------------------------
def render_scene(scene_name, seed, output_base):

    # Limpiar escena
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    scene = bpy.context.scene
    random.seed(seed)

    # Carpeta de salida
    output_folder = os.path.join(output_base, scene_name)
    os.makedirs(output_folder, exist_ok=True)

    # Parámetros de animación
    scene.frame_start         = 1
    scene.frame_end           = 10
    scene.render.fps          = 24
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720

    num_frames = scene.frame_end - scene.frame_start + 1

    # --------------------------------------------------
    # FONDO TRANSPARENTE (canal alfa en PNG)
    # Sin suelo: Los objetos quedan recortados sobre
    # fondo transparente/blanco para detección por silueta
    # --------------------------------------------------
    scene.render.film_transparent = True
    scene.render.image_settings.file_format      = 'PNG'
    scene.render.image_settings.color_mode       = 'RGBA'
    scene.render.image_settings.compression      = 15

    # Motor de render: CYCLES para transparencia real
    # (EEVEE también soporta film_transparent)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64          # suficiente para siluetas nítidas
    scene.cycles.use_denoising = True

    # ---- Material blanco ----
    white = get_white_material()

    # ---- SIN SUELO — se omite el plano para que el fondo sea transparente ----
    # (Si prefieres suelo semitransparente, descomenta el bloque siguiente)
    # bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    # ground = bpy.context.object
    # ground.name = "Ground"
    # mat_transp = bpy.data.materials.new("GroundTransp")
    # mat_transp.use_nodes = True
    # mat_transp.blend_method = 'BLEND'
    # bsdf = mat_transp.node_tree.nodes["Principled BSDF"]
    # bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    # bsdf.inputs["Alpha"].default_value = 0.0
    # ground.data.materials.append(mat_transp)

    # Objetos aleatorios (misma lógica y semilla)
    for _ in range(NUM_OBJECTS):
        add_random_object(white)

    # --------------------------------------------------
    # ILUMINACIÓN A CONTRALUZ
    # La luz viene de DEBAJO de la escena (Z negativa),
    # atravesando el fondo transparente y recortando las
    # siluetas de los objetos vistos desde arriba.
    #
    # Complementamos con una luz muy débil cenital para
    # que los objetos no sean negro absoluto (opcional:
    # si quieres siluetas puras en negro, elimínala).
    # --------------------------------------------------

    # Luz principal: contraluz desde abajo
    bpy.ops.object.light_add(type='SUN', location=(0, 0, -distance))
    backlight = bpy.context.object
    backlight.name = "Backlight"
    backlight.data.energy = 8.0
    backlight.data.angle  = math.radians(2)   # muy colimada → silueta limpia
    # Apuntar hacia arriba (+Z) para iluminar de abajo hacia arriba
    backlight.rotation_euler = (math.pi, 0, 0)   # girar 180° en X → apunta a +Z

    # Luz de relleno cenital muy tenue (da algo de textura a los objetos)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, distance))
    toplight = bpy.context.object
    toplight.name = "TopFill"
    toplight.data.energy = 0.8
    toplight.data.angle  = math.radians(30)
    toplight.rotation_euler = (0, 0, 0)

    # --------------------------------------------------
    # CÁMARA FIJA. vista cenital (top-down, 90°)
    # Apunta directamente hacia abajo desde Z = distance
    # --------------------------------------------------
    bpy.ops.object.camera_add(location=(0, 0, distance))
    cam = bpy.context.object
    cam.name  = "TopCamera"
    cam.data.lens = 35          # algo más abierta para ver toda la escena
    cam.data.type = 'ORTHO'     # ortográfica → sin distorsión perspectiva
    cam.data.ortho_scale = 16   # cubre ±8 u en cada eje (pos_range=6 + margen)
    scene.camera = cam

    # Orientar la cámara mirando hacia abajo (-Z)
    cam.rotation_euler = (0, 0, 0)   # con tipo ORTHO y loc en +Z apunta a -Z por defecto

    # TrackTo al origen (por si acaso)
    cam_target = bpy.data.objects.new("CamTarget", None)
    cam_target.location = (0, 0, 0)
    bpy.context.collection.objects.link(cam_target)

    cam_constraint = cam.constraints.new(type='TRACK_TO')
    cam_constraint.target     = cam_target
    cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    cam_constraint.up_axis    = 'UP_Y'

    # Cámara FIJA, sin keyframes de posición

    # --------------------------------------------------
    # ANIMACIÓN DE LA LUZ A CONTRALUZ
    # La luz orbita en el plano XZ inferior (Z negativa)
    # describiendo el mismo arco de 90° que la cámara
    # en la escena 1, pero en el hemisferio inferior.
    # Esto varía el ángulo de incidencia del contraluz
    # manteniendo siempre el efecto de silueta.
    # --------------------------------------------------
    for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
        t     = i / (num_frames - 1)          # 0 → 1
        theta = (math.pi / 2) * (1 - t)       # π/2 → 0  (directamente abajo → lateral)

        lx =  distance * math.cos(theta)
        ly =  0.0
        lz = -distance * math.sin(theta)      # Z negativa → hemisferio inferior

        backlight.location = (lx, ly, lz)

        # La rotación debe actualizarse también para que siga apuntando a +Z
        # Calculamos el vector de dirección hacia el origen desde la posición de la luz
        # y lo convertimos en ángulos de Euler para la SUN
        import mathutils
        dir_vec = mathutils.Vector((0, 0, 0)) - mathutils.Vector((lx, ly, lz))
        dir_vec.normalize()
        rot_quat = dir_vec.to_track_quat('Z', 'Y')
        backlight.rotation_euler = rot_quat.to_euler()

        backlight.keyframe_insert(data_path="location",       frame=frame)
        backlight.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Interpolación lineal
    if backlight.animation_data and backlight.animation_data.action:
        for fcurve in backlight.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

    # Render
    scene.render.filepath = output_folder + "\\"

    print(f"\n{'='*50}")
    print(f"Renderizando escena: {scene_name}")
    print(f"Semilla: {seed}  |  Objetos: {NUM_OBJECTS}")
    print(f"Vista: cenital ortográfica | Fondo: transparente (RGBA)")
    print(f"Luz contraluz orbita en hemisferio inferior (Z<0)")
    print(f"Carpeta: {output_folder}")
    print(f"{'='*50}\n")

    bpy.ops.render.render(animation=True)
    print(f"✓ Escena {scene_name} completada.\n")


# --------------------------------------------------
# EJECUTAR LAS 3 ESCENAS
# --------------------------------------------------
output_folder = os.path.join(base_output_folder, "escena3")
os.makedirs(output_folder, exist_ok=True)

for idx, sname in enumerate(scene_names):
    render_scene(
        scene_name  = sname,
        seed        = SEED_BASE + idx,
        output_base = output_folder,
    )

print("\nLas 3 escenas de la escena 3 han sido renderizadas correctamente.")
print(f"Resultados en: {output_folder}")