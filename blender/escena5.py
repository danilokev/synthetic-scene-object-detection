import bpy
import math
import random
import os


# --------------------------------------------------
# CONFIGURACIÓN BASE
# --------------------------------------------------

base_output_folder = r"C:\Users\PC\OneDrive\Escritorio\UNI\IVC\TrabajoIvc\salidas" #CAMBIAR ESTA RUTA!!

scene_names = ["escena5_1", "escena5_2", "escena5_3"]

NUM_OBJECTS = 12
SEED_BASE   = 42
distance    = 25.0

# --------------------------------------------------
# COLORES BASE (se usan dentro de las texturas)
# --------------------------------------------------
COLORS = {
    "rojo":     (1.0, 0.0, 0.0, 1.0),
    "verde":    (0.0, 0.8, 0.0, 1.0),
    "azul":     (0.0, 0.2, 1.0, 1.0),
    "amarillo": (1.0, 0.9, 0.0, 1.0),
    "naranja":  (1.0, 0.4, 0.0, 1.0),
}

TEXTURE_TYPES = ["CHECKER", "BRICK", "VORONOI"]

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
# MATERIAL CON TEXTURA PROCEDIMENTAL ALEATORIA
# --------------------------------------------------
def get_textured_material():
    color_name, color_value = random.choice(list(COLORS.items()))
    tex_type = random.choice(TEXTURE_TYPES)
    mat_name = f"Mat_{tex_type}_{color_name}_{random.randint(0, 99999)}"

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Limpiar nodos por defecto
    nodes.clear()

    # Nodo de salida
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    # BSDF Principled
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Roughness"].default_value = 0.5
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Coordenadas de textura
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-600, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-400, 0)
    # Escala aleatoria para variar la frecuencia del patrón
    scale_val = random.uniform(2.0, 6.0)
    mapping.inputs["Scale"].default_value = (scale_val, scale_val, scale_val)
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

    if tex_type == "CHECKER":
        tex_node = nodes.new("ShaderNodeTexChecker")
        tex_node.location = (-100, 0)
        # Color1 = color aleatorio, Color2 = blanco
        tex_node.inputs["Color1"].default_value = color_value
        tex_node.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        tex_node.inputs["Scale"].default_value  = random.uniform(3.0, 8.0)
        links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    elif tex_type == "BRICK":
        tex_node = nodes.new("ShaderNodeTexBrick")
        tex_node.location = (-100, 0)
        tex_node.inputs["Color1"].default_value  = color_value
        tex_node.inputs["Color2"].default_value  = (1.0, 1.0, 1.0, 1.0)
        tex_node.inputs["Mortar"].default_value  = (0.1, 0.1, 0.1, 1.0)
        tex_node.inputs["Scale"].default_value   = random.uniform(3.0, 8.0)
        tex_node.inputs["Mortar Size"].default_value = 0.05
        links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    elif tex_type == "VORONOI":
        tex_node = nodes.new("ShaderNodeTexVoronoi")
        tex_node.location = (-100, 100)
        tex_node.inputs["Scale"].default_value = random.uniform(3.0, 8.0)
        links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])

        # MixRGB: mezcla el color base con el output de Voronoi
        mix_node = nodes.new("ShaderNodeMixRGB")
        mix_node.location = (100, 0)
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs["Fac"].default_value = 1.0
        mix_node.inputs["Color1"].default_value = color_value
        links.new(tex_node.outputs["Distance"], mix_node.inputs["Color2"])
        links.new(mix_node.outputs["Color"],    bsdf.inputs["Base Color"])

    return mat


# --------------------------------------------------
# TIPOS DE OBJETOS
# --------------------------------------------------
OBJECT_TYPES = [
    "CUBE", "CYLINDER", "RECT_PRISM",
    "SPHERE", "CONE", "TORUS", "MONKEY",
]

def add_random_object(pos_range=6.0, scale_min=0.4, scale_max=1.5):
    obj_type = random.choice(OBJECT_TYPES)
    mat = get_textured_material()
    s   = random.uniform(scale_min, scale_max)
    px  = random.uniform(-pos_range, pos_range)
    py  = random.uniform(-pos_range, pos_range)

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

    # Aplicar textura
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    # Añadir UV unwrap para que las texturas se vean bien
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.uv.smart_project(angle_limit=66.0)
    bpy.ops.object.editmode_toggle()

    if obj_type in ("SPHERE", "CONE", "TORUS", "MONKEY"):
        bpy.ops.object.shade_smooth()

    return obj


# --------------------------------------------------
# FUNCIÓN PRINCIPAL
# --------------------------------------------------
def render_scene(scene_name, seed, output_base):

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
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

    # Objetos con textura
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
        t     = i / (num_frames - 1)
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
output_folder = os.path.join(base_output_folder, "escena5")
os.makedirs(output_folder, exist_ok=True)

for idx, sname in enumerate(scene_names):
    render_scene(
        scene_name  = sname,
        seed        = SEED_BASE + idx,
        output_base = output_folder,
    )

print("\n✓✓✓ Las 3 escenas de la Escena 5 han sido renderizadas correctamente.")
print(f"Resultados en: {output_folder}")