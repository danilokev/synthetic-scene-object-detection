import bpy
import math
from mathutils import Vector
from datetime import datetime

import os


# --------------------------------------------------
# LIMPIAR ESCENA
# --------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------
output_folder = "TU RUTA AQUI\\proyectoVideo"   # cambia esta ruta

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_folder = f"{output_folder}/{timestamp}/"

os.makedirs(output_folder, exist_ok=True)



# --------------------------------------------------
# PARÁMETROS DE ANIMACIÓN
# --------------------------------------------------
scene.frame_start = 1
scene.frame_end = 10
scene.render.fps = 24
scene.render.resolution_x = 720
scene.render.resolution_y = 720

distance = 25.0

num_frames = scene.frame_end - scene.frame_start + 1


# --------------------------------------------------
# SUELO
# --------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.object

# Material blanco para el suelo
ground_mat = bpy.data.materials.new(name="GroundWhite")
ground_mat.use_nodes = True
ground_bsdf = ground_mat.node_tree.nodes["Principled BSDF"]
ground_bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
ground.data.materials.append(ground_mat)


# --------------------------------------------------
# OBJETOS
# --------------------------------------------------
def create_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    return mat

# Diccionario de materiales
materials = {
    "white": create_material("White", (1, 1, 1)),
    "red": create_material("Red", (1, 0, 0)),
    "blue": create_material("Blue", (0, 0, 1)),
    "green": create_material("Green", (0, 1, 0)),
    "yellow": create_material("Yellow", (1, 1, 0)),
    "orange": create_material("Orange", (1, 0.5, 0)),
    "black": create_material("Black", (0, 0, 0)),
}

# Cubo central
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.6))
cube = bpy.context.object
cube.data.materials.append(materials["white"])

# ToDo: añadir resto de objetos




# --------------------------------------------------
# LUZ TIPO SUN
# --------------------------------------------------
bpy.ops.object.light_add(type='SUN', location=(0, 0, distance))
sun = bpy.context.object
sun.data.energy = 3.5

# --------------------------------------------------
# CÁMARA
# --------------------------------------------------
bpy.ops.object.camera_add(location=(0, 0, distance))
cam = bpy.context.object
cam.name = "OrbitCamera"
cam.data.lens = 50
scene.camera = cam

# --------------------------------------------------
# TRACK TO: la cámara siempre mira al origen
# --------------------------------------------------
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0)
bpy.context.collection.objects.link(target)

constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = target
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

# --------------------------------------------------
# KEYFRAMES DE ÓRBITA CIRCULAR (esto hay otras formas mas elegantes con blender pero se puede hacer así en código)
# --------------------------------------------------
for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
    t = i / (num_frames - 1)

    # De arriba (0,0,distance) a la derecha (distance,0,0)
    theta = (math.pi / 2) * (1 - t)

    x = distance * math.cos(theta)
    y = 0.0
    z = distance * math.sin(theta)

    cam.location = (x, y, z)
    cam.keyframe_insert(data_path="location", frame=frame)

# --------------------------------------------------
# INTERPOLACIÓN LINEAL (esto no haría falta pero bien, por si se quieren hacer animaciones con mas frames
# --------------------------------------------------
if cam.animation_data and cam.animation_data.action:
    action = cam.animation_data.action
    if hasattr(action, "fcurves"):
        for fcurve in action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'


# --------------------------------------------------
# SALIDA
# --------------------------------------------------
scene.render.filepath = output_folder
scene.render.image_settings.file_format = 'PNG'

print("Animación circular creada.")

# --------------------------------------------------
# RENDER ANIMACIÓN
# --------------------------------------------------

# comenta lo siguiente para que no se genera la animación y poder ver la escena en blender
bpy.ops.render.render(animation=True)