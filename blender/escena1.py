import bpy
import math
import random
from mathutils import Vector
import os


# --------------------------------------------------
# CONFIGURACIÓN BASE
# --------------------------------------------------

base_output_folder = r"C:\Users\leigh\IVC\proyecto_ivc\datos" #CAMBIAR ESTA RUTA!!

scene_names = ["escena1_1", "escena1_2", "escena1_3"]

NUM_OBJECTS = 12       # Objetos por escena
SEED_BASE   = 42       # Semilla base (cada escena suma su índice)

distance = 25.0


# --------------------------------------------------
# MATERIAL BLANCO (único, reutilizable)
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
# --------------------------------------------------
# Tipos "2D" (proyección simple): CYLINDER, RECTANGULAR PRISM (cube escalado), CUBE
# Tipos "3D":                     SPHERE, CONE, TORUS, MONKEY

OBJECT_TYPES = [
    "CUBE",          # proyección simple
    "CYLINDER",      # proyección simple
    "RECT_PRISM",    # proyección simple (cubo muy aplanado)
    "SPHERE",        # 3D
    "CONE",          # 3D
    "TORUS",         # 3D
    "MONKEY",        # 3D
]

def add_random_object(mat, pos_range=6.0, scale_min=0.4, scale_max=1.5):
    """Añade un objeto aleatorio con posición y escala aleatorias."""
    obj_type = random.choice(OBJECT_TYPES)

    # Escala aleatoria uniforme
    s = random.uniform(scale_min, scale_max)

    # Posición aleatoria en XY, Z para que descansen sobre el suelo (Z = s/2 aprox)
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
        # Prisma rectangular: escala no uniforme
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
        # El torus ya está centrado; lo elevamos su radio mayor + menor
        major_r = 0.4 * s
        minor_r = 0.15 * s
        bpy.ops.mesh.primitive_torus_add(major_radius=major_r,
                                          minor_radius=minor_r,
                                          location=(px, py, minor_r + 0.05))
        obj = bpy.context.object

    elif obj_type == "MONKEY":
        bpy.ops.mesh.primitive_monkey_add(size=s, location=(px, py, s * 0.5))
        obj = bpy.context.object

    # Aplicar material blanco
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    # Smooth shading para esferas, conos, toroides y monkey
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

    # Limpiar mallas huérfanas para no acumular basura entre escenas
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    scene = bpy.context.scene
    random.seed(seed)

    # ---- Carpeta de salida ----
    output_folder = os.path.join(output_base, scene_name)
    os.makedirs(output_folder, exist_ok=True)

    # ---- Parámetros de animación ----
    scene.frame_start = 1
    scene.frame_end   = 10
    scene.render.fps  = 24
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

    # ---- Objetos aleatorios ----
    for _ in range(NUM_OBJECTS):
        add_random_object(white)

    # ---- Luz Solar ----
    bpy.ops.object.light_add(type='SUN', location=(5, -5, distance))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.angle  = math.radians(5)   # sombras más definidas

    # Segunda luz de relleno (suave, desde abajo-frente)
    bpy.ops.object.light_add(type='AREA', location=(0, -8, 6))
    fill = bpy.context.object
    fill.data.energy = 200
    fill.scale = (4, 4, 1)

    # ---- Cámara ----
    bpy.ops.object.camera_add(location=(0, 0, distance))
    cam = bpy.context.object
    cam.name = "OrbitCamera"
    cam.data.lens = 50
    scene.camera = cam

    # Target para TrackTo
    target = bpy.data.objects.new("CamTarget", None)
    target.location = (0, 0, 0)
    bpy.context.collection.objects.link(target)

    constraint = cam.constraints.new(type='TRACK_TO')
    constraint.target    = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis    = 'UP_Y'

    # ---- Animación: arco de 90° (cenital → lateral) ----
    for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
        t = i / (num_frames - 1)
        theta = (math.pi / 2) * (1 - t)   # 90° → 0°

        x = distance * math.cos(theta)
        y = 0.0
        z = distance * math.sin(theta)

        cam.location = (x, y, z)
        cam.keyframe_insert(data_path="location", frame=frame)

    # Interpolación lineal
    if cam.animation_data and cam.animation_data.action:
        for fcurve in cam.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

    # ---- Render ----
    scene.render.filepath = output_folder + "\\"
    scene.render.image_settings.file_format = 'PNG'

    print(f"\n{'='*50}")
    print(f"Renderizando escena: {scene_name}")
    print(f"Semilla: {seed}  |  Objetos: {NUM_OBJECTS}")
    print(f"Carpeta: {output_folder}")
    print(f"{'='*50}\n")

    bpy.ops.render.render(animation=True)
    print(f"✓ Escena {scene_name} completada.\n")


# --------------------------------------------------
# EJECUTAR LAS 3 ESCENAS
# --------------------------------------------------
output_folder = os.path.join(base_output_folder, "escena1")
os.makedirs(output_folder, exist_ok=True)

for idx, sname in enumerate(scene_names):
    render_scene(
        scene_name  = sname,
        seed        = SEED_BASE + idx,   # semilla distinta → objetos distintos
        output_base = output_folder,
    )

print("\n✓✓✓ Las 3 escenas han sido renderizadas correctamente.")
print(f"Resultados en: {output_folder}")