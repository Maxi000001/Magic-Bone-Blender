bl_info = {
    "name": "Magic Bone",
    "author": "Malik & ChatGPT",
    "version": (0, 8),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Magic Bone",
    "description": "Create bones by normals, by axis, and between 2 vertices",
    "category": "Rigging",
}

import bpy
import bmesh
from bpy.types import Operator, Panel
from mathutils import Vector

# === 1. НОРМАЛИ ===
def create_bones_from_normals(context, length=0.2, invert=False):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return

    original_mode = obj.mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    verts_data = [(obj.matrix_world @ v.co, v.normal.normalized()) for v in bm.verts if v.select]
    
    bpy.ops.object.mode_set(mode='OBJECT')

    if not verts_data:
        bpy.ops.object.mode_set(mode=original_mode)
        return

    arm = next((o for o in context.selected_objects if o.type == 'ARMATURE'), None)
    if arm is None:
        arm = bpy.data.objects.new("MagicArmature", bpy.data.armatures.new("MagicArmature"))
        context.collection.objects.link(arm)

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')

    for co, normal in verts_data:
        direction = -normal if invert else normal
        bone = arm.data.edit_bones.new("Bone_Normal")
        bone.head = co
        bone.tail = co + direction * length

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode=original_mode)
    
# === 2. ОСИ ===
def create_bones_by_axis(context, axis='X', length=0.2, negative=False):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return

    original_mode = obj.mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    verts_world_coords = [obj.matrix_world @ v.co for v in bm.verts if v.select]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    if not verts_world_coords:
        bpy.ops.object.mode_set(mode=original_mode)
        return

    arm = next((o for o in context.selected_objects if o.type == 'ARMATURE'), None)
    if arm is None:
        arm = bpy.data.objects.new("MagicArmature", bpy.data.armatures.new("MagicArmature"))
        context.collection.objects.link(arm)

    direction = Vector((1,0,0)) if axis=='X' else Vector((0,1,0)) if axis=='Y' else Vector((0,0,1))
    if negative:
        direction = -direction

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')

    for co in verts_world_coords:
        bone = arm.data.edit_bones.new(f"Bone_{axis}{'-' if negative else '+'}")
        bone.head = co
        bone.tail = co + direction * length

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode=original_mode)

# === 3. МЕЖДУ ВЕРШИН ===
def create_bone_between_vertices(context, invert=False):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return

    original_mode = obj.mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    
    selected_verts = [v for v in bm.verts if v.select]
    active_vert = bm.select_history.active
    
    if len(selected_verts) != 2 or not active_vert:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode=original_mode)
        print("Нужно выбрать ровно 2 вершины и сделать одну из них активной (последней выделенной)")
        return
    
    # Получаем мировые координаты
    p1 = obj.matrix_world @ active_vert.co
    
    # Находим вторую вершину, которая не является активной
    non_active_vert = next(v for v in selected_verts if v != active_vert)
    p2 = obj.matrix_world @ non_active_vert.co
    
    bpy.ops.object.mode_set(mode='OBJECT')

    # ✅ ИСПРАВЛЕНИЕ: МЕНЯЕМ ЛОГИКУ ДЛЯ КНОПКИ "МЕЖДУ ВЕРШИН"
    # Без галочки "Invert" (invert == False), мы инвертируем кость
    # С галочкой "Invert" (invert == True), мы не инвертируем
    if not invert:
        p1, p2 = p2, p1

    arm = next((o for o in context.selected_objects if o.type == 'ARMATURE'), None)
    if arm is None:
        arm = bpy.data.objects.new("MagicArmature", bpy.data.armatures.new("MagicArmature"))
        context.collection.objects.link(arm)

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')

    bone = arm.data.edit_bones.new("Bone_Between")
    bone.head = p1
    bone.tail = p2

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode=original_mode)
    
# === ОПЕРАТОРЫ ===
class MBONE_OT_AddNormal(Operator):
    bl_idname = "mbone.add_normal"
    bl_label = "Add Normal Bones"

    length: bpy.props.FloatProperty(name="Length", default=0.2)
    invert: bpy.props.BoolProperty(name="Invert", default=False)

    def execute(self, context):
        create_bones_from_normals(context, self.length, self.invert)
        return {'FINISHED'}

class MBONE_OT_AddByAxis(Operator):
    bl_idname = "mbone.add_by_axis"
    bl_label = "Add Bones By Axis"

    axis: bpy.props.EnumProperty(items=[
        ('X', "X+", ""),
        ('Y', "Y+", ""),
        ('Z', "Z+", ""),
        ('X-', "X-", ""),
        ('Y-', "Y-", ""),
        ('Z-', "Z-", ""),
    ], name="Axis")

    length: bpy.props.FloatProperty(name="Length", default=0.2)

    def execute(self, context):
        axis = self.axis[0]
        negative = self.axis.endswith('-')
        create_bones_by_axis(context, axis, self.length, negative)
        return {'FINISHED'}

class MBONE_OT_AddBetweenVertices(Operator):
    bl_idname = "mbone.add_between_vertices"
    bl_label = "Add Bone Between 2 Vertices"

    invert: bpy.props.BoolProperty(name="Invert", default=False)

    def execute(self, context):
        create_bone_between_vertices(context, self.invert)
        return {'FINISHED'}

# === ПАНЕЛЬ ===
class MBONE_PT_Panel(Panel):
    bl_label = "Magic Bone"
    bl_idname = "MBONE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Magic Bone'

    def draw(self, context):
        layout = self.layout

        # --- Блок 1: Normals ---
        box = layout.box()
        box.label(text="From Normals:")
        op = box.operator("mbone.add_normal", text="Add Normal Bones")
        op.length = context.scene.mbone_normal_length
        op.invert = context.scene.mbone_normal_invert
        box.prop(context.scene, "mbone_normal_length")
        box.prop(context.scene, "mbone_normal_invert")

        # --- Блок 2: By Axis ---
        box = layout.box()
        box.label(text="By Axis:")
        for axis_row in [('X', 'Y', 'Z'), ('X-', 'Y-', 'Z-')]:
            row = box.row(align=True)
            for axis in axis_row:
                op = row.operator("mbone.add_by_axis", text=axis)
                op.axis = axis
                op.length = context.scene.mbone_axis_length
        box.prop(context.scene, "mbone_axis_length")

        # --- Блок 3: Between Vertices ---
        box = layout.box()
        box.label(text="Between 2 Vertices:")
        op = box.operator("mbone.add_between_vertices", text="Add Bone Between")
        op.invert = context.scene.mbone_between_invert
        box.prop(context.scene, "mbone_between_invert")

# === РЕГИСТРАЦИЯ ===
classes = (
    MBONE_OT_AddNormal,
    MBONE_OT_AddByAxis,
    MBONE_OT_AddBetweenVertices,
    MBONE_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # UI props
    bpy.types.Scene.mbone_normal_length = bpy.props.FloatProperty(name="Length", default=0.2)
    bpy.types.Scene.mbone_normal_invert = bpy.props.BoolProperty(name="Invert", default=False)
    bpy.types.Scene.mbone_axis_length = bpy.props.FloatProperty(name="Length", default=0.2)
    bpy.types.Scene.mbone_between_invert = bpy.props.BoolProperty(name="Invert", default=False)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.mbone_normal_length
    del bpy.types.Scene.mbone_normal_invert
    del bpy.types.Scene.mbone_axis_length
    del bpy.types.Scene.mbone_between_invert

if __name__ == "__main__":
    register()