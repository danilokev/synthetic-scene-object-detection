import bpy
import math
import random
import os


# --------------------------------------------------
# CONFIGURACIÓN BASE
# --------------------------------------------------

base_output_folder = r"C:\Users\PC\OneDrive\Escritorio\UNI\IVC\TrabajoIvc\salidas" #CAMBIAR ESTA RUTA!!

scene_names = ["escena2_1", "escena2_2", "escena2_3"]

NUM_OBJECTS = 12      # Mismo número que escena 1
SEED_BASE   = 42      # Mismas semillas → mismos objetos que escena 1

distance = 25.0       # Radio de la órbita de la luz (= distancia cámara escena 1)


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


# --------------------------------------------------
# CREACIÓN DE OBJETOS ALEATORIOS
# (Idéntica a escena 1 — mismas semillas → misma disposición)
# --------------------------------------------------
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

    # ---- Limpiar escena ----
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    scene = bpy.context.scene
    random.seed(seed)

    # ---- Carpeta de salida ----
    output_folder = os.path.join(output_base, scene_name)
    os.makedirs(output_folder, exist_ok=True)

    # ---- Parámetros de animación ----
    scene.frame_start      = 1
    scene.frame_end        = 10
    scene.render.fps       = 24
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720

    num_frames = scene.frame_end - scene.frame_start + 1

    # ---- Material blanco ----
    white = get_white_material()

    # ---- Suelo blanco ----
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    if ground.data.materials:
        ground.data.materials[0] = white
    else:
        ground.data.materials.append(white)

    # ---- Objetos aleatorios (misma lógica y semilla que escena 1) ----
    for _ in range(NUM_OBJECTS):
        add_random_object(white)

    # --------------------------------------------------
    # LUZ PRINCIPAL (SUN) — se animará en órbita
    # Posición inicial: cenital (θ = 90°) → lateral (θ = 0°)
    # Mismo arco que seguía la cámara en la escena 1.
    # --------------------------------------------------
    # Posición de arranque (frame 1): directamente encima
    bpy.ops.object.light_add(type='SUN', location=(0, 0, distance))
    sun = bpy.context.object
    sun.name = "OrbitSun"
    sun.data.energy = 5.0          # algo más de energía para compensar la falta de relleno
    sun.data.angle  = math.radians(3)   # sombras nítidas para análisis

    # Apuntar siempre al origen con TrackTo
    sun_target = bpy.data.objects.new("SunTarget", None)
    sun_target.location = (0, 0, 0)
    bpy.context.collection.objects.link(sun_target)

    sun_constraint = sun.constraints.new(type='TRACK_TO')
    sun_constraint.target     = sun_target
    sun_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    sun_constraint.up_axis    = 'UP_Y'

    # ---- Luz de ambiente muy tenue (evita negros absolutos) ----
    # Usamos un AREA de energía baja en posición fija cenital
    bpy.ops.object.light_add(type='AREA', location=(0, 0, distance * 0.6))
    ambient = bpy.context.object
    ambient.name = "AmbientFill"
    ambient.data.energy = 40        # muy suave — sólo evita zonas en negro total
    ambient.scale = (10, 10, 1)
    ambient.rotation_euler = (0, 0, 0)

    # --------------------------------------------------
    # CÁMARA FIJA — misma posición que el frame 1 de la
    # escena 1 (cenital, mirando hacia abajo)
    # --------------------------------------------------
    cam_x = distance * math.cos(math.radians(45))  # 45° de elevación: vista diagonal
    cam_z = distance * math.sin(math.radians(45))  # equilibrio entre cenital y lateral

    bpy.ops.object.camera_add(location=(cam_x, 0, cam_z))
    cam = bpy.context.object
    cam.name  = "FixedCamera"
    cam.data.lens = 50
    scene.camera = cam

    # TrackTo para que apunte siempre al origen
    cam_target = bpy.data.objects.new("CamTarget", None)
    cam_target.location = (0, 0, 0)
    bpy.context.collection.objects.link(cam_target)

    cam_constraint = cam.constraints.new(type='TRACK_TO')
    cam_constraint.target     = cam_target
    cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    cam_constraint.up_axis    = 'UP_Y'

    # La cámara es FIJA → NO se insertan keyframes de posición

    # --------------------------------------------------
    # ANIMACIÓN DE LA LUZ — misma trayectoria que la
    # cámara en la escena 1: arco de 90° (cenital→lateral)
    # plano XZ, girando en el plano Y=0
    # --------------------------------------------------
    for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
        t     = i / (num_frames - 1)           # 0 → 1
        theta = (math.pi / 2) * (1 - t)        # π/2 → 0  (cenital → lateral)

        lx = distance * math.cos(theta)
        ly = 0.0
        lz = distance * math.sin(theta)

        sun.location = (lx, ly, lz)
        sun.keyframe_insert(data_path="location", frame=frame)

    # Interpolación lineal para la luz
    if sun.animation_data and sun.animation_data.action:
        for fcurve in sun.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

    # ---- Render ----
    scene.render.filepath = output_folder + "\\"
    scene.render.image_settings.file_format = 'PNG'

    print(f"\n{'='*50}")
    print(f"Renderizando escena: {scene_name}")
    print(f"Semilla: {seed}  |  Objetos: {NUM_OBJECTS}")
    print(f"Cámara FIJA en ({cam_x:.1f}, 0, {cam_z:.1f})")
    print(f"Luz orbita 90° (cenital → lateral) en plano XZ")
    print(f"Carpeta: {output_folder}")
    print(f"{'='*50}\n")

    bpy.ops.render.render(animation=True)
    print(f"✓ Escena {scene_name} completada.\n")


# --------------------------------------------------
# EJECUTAR LAS 3 ESCENAS
# --------------------------------------------------
output_folder = os.path.join(base_output_folder, "escena2")
os.makedirs(output_folder, exist_ok=True)

for idx, sname in enumerate(scene_names):
    render_scene(
        scene_name  = sname,
        seed        = SEED_BASE + idx,   # mismas semillas → misma distribución de objetos
        output_base = output_folder,
    )

print("\n✓✓✓ Las 3 escenas de la escena 2 han sido renderizadas correctamente.")
print(f"Resultados en: {output_folder}")