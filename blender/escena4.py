import bpy
import math
import random
from mathutils import Vector
import os


# --------------------------------------------------
# CONFIGURACIÓN BASE
# --------------------------------------------------

base_output_folder = r"C:\Users\PC\OneDrive\Escritorio\UNI\IVC\TrabajoIvc\salidas" #CAMBIAR ESTA RUTA!!

scene_names = ["escena4_1", "escena4_2", "escena4_3"]

NUM_OBJECTS = 12
SEED_BASE   = 42

distance = 25.0

# --------------------------------------------------
# COLORES DISPONIBLES (RGBA)
# --------------------------------------------------
COLORS = {
    "rojo":     (1.0, 0.0, 0.0, 1.0),
    "verde":    (0.0, 0.8, 0.0, 1.0),
    "azul":     (0.0, 0.2, 1.0, 1.0),
    "amarillo": (1.0, 0.9, 0.0, 1.0),
    "naranja":  (1.0, 0.4, 0.0, 1.0),
}

# --------------------------------------------------
# MATERIAL BLANCO (para el suelo)
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
# MATERIAL DE COLOR ALEATORIO (único por objeto)
# --------------------------------------------------
def get_random_color_material():
    color_name, color_value = random.choice(list(COLORS.items()))
    # Nombre único para no reutilizar entre objetos
    mat_name = f"Mat_{color_name}_{random.randint(0, 99999)}"
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color_value
    bsdf.inputs["Roughness"].default_value  = 0.5
    return mat


# --------------------------------------------------
# TIPOS DE OBJETOS
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

def add_random_object(pos_range=6.0, scale_min=0.4, scale_max=1.5):
    """Añade un objeto aleatorio con color aleatorio."""
    obj_type = random.choice(OBJECT_TYPES)
    mat = get_random_color_material()  # color único por objeto
    s = random.uniform(scale_min, scale_max)

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

    # Aplicar material de color
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

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    # Limpiar materiales huérfanos entre escenas
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

    scene = bpy.context.scene
    random.seed(seed)

    output_folder = os.path.join(output_base, scene_name)
    os.makedirs(output_folder, exist_ok=True)

    scene.frame_start = 1
    scene.frame_end   = 10
    scene.render.fps  = 24
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720

    num_frames = scene.frame_end - scene.frame_start + 1

    white = get_white_material()

    # Suelo blanco
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    if ground.data.materials:
        ground.data.materials[0] = white
    else:
        ground.data.materials.append(white)

    # Objetos con color aleatorio
    for _ in range(NUM_OBJECTS):
        add_random_object()

    # Luz Solar
    bpy.ops.object.light_add(type='SUN', location=(5, -5, distance))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.angle  = math.radians(5)

    # Luz de relleno
    bpy.ops.object.light_add(type='AREA', location=(0, -8, 6))
    fill = bpy.context.object
    fill.data.energy = 200
    fill.scale = (4, 4, 1)

    # Cámara
    bpy.ops.object.camera_add(location=(0, 0, distance))
    cam = bpy.context.object
    cam.name = "OrbitCamera"
    cam.data.lens = 50
    scene.camera = cam

    target = bpy.data.objects.new("CamTarget", None)
    target.location = (0, 0, 0)
    bpy.context.collection.objects.link(target)

    constraint = cam.constraints.new(type='TRACK_TO')
    constraint.target     = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis    = 'UP_Y'

    # Animación: arco de 90°
    for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
        t = i / (num_frames - 1)
        theta = (math.pi / 2) * (1 - t)

        x = distance * math.cos(theta)
        y = 0.0
        z = distance * math.sin(theta)

        cam.location = (x, y, z)
        cam.keyframe_insert(data_path="location", frame=frame)

    if cam.animation_data and cam.animation_data.action:
        for fcurve in cam.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

    # Render
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
output_folder = os.path.join(base_output_folder, "escena4")
os.makedirs(output_folder, exist_ok=True)

for idx, sname in enumerate(scene_names):
    render_scene(
        scene_name  = sname,
        seed        = SEED_BASE + idx,
        output_base = output_folder,
    )

print("\n✓✓✓ Las 3 escenas de la Escena 4 han sido renderizadas correctamente.")
print(f"Resultados en: {output_folder}")