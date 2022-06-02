# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "ACON3D Panel",
    "description": "",
    "author": "hoie@acon3d.com",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "ACON3D",
}


import bpy
from .lib.tracker import tracker


class MATERIAL_UL_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        layout.use_property_split = True
        layout.use_property_decorate = False
        ob = data
        slot = item
        if ma := slot.material:
            layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            layout.prop(ma.ACON_prop, "type", text="")

            toonNode = ma.node_tree.nodes.get("ACON_nodeGroup_combinedToon")

            if not toonNode:
                return

            if ma.ACON_prop.type == "Diffuse":
                layout.label(text="", translate=False)

            if ma.ACON_prop.type == "Mirror":
                layout.prop(toonNode.inputs[6], "default_value", text="")

            if ma.ACON_prop.type == "Glow":
                layout.prop(toonNode.inputs[5], "default_value", text="")

            if ma.ACON_prop.type == "Clear":
                layout.prop(toonNode.inputs[7], "default_value", text="")


class CloneMaterialOperator(bpy.types.Operator):
    """Clone selected material"""

    bl_idname = "acon3d.clone_material"
    bl_label = "Clone Material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        try:
            return bool(context.object.active_material)
        except:
            return False

    def execute(self, context):
        mat = context.object.active_material.copy()
        context.object.active_material = mat

        return {"FINISHED"}


class MaterialPanel(bpy.types.Panel):
    bl_parent_id = "ACON_PT_Face_Main"
    bl_idname = "ACON_PT_Material"
    bl_label = "Object Material"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        row = layout.row()

        if obj:
            col = row.column()
            col.scale_x = 3
            col.separator()
            col = row.column()
            col.template_list(
                "MATERIAL_UL_List",
                "",
                obj,
                "material_slots",
                obj,
                "active_material_index",
                rows=2,
            )
            if mat := obj.active_material:
                box = col.box()
                row = box.row()
                row.template_ID(
                    obj, "active_material", new="acon3d.clone_material", unlink=""
                )
                row = box.row()
                row.prop(mat.ACON_prop, "toggle_shadow")
                row = box.row()
                row.prop(mat.ACON_prop, "toggle_shading")
                row = box.row()
                row.prop(mat.ACON_prop, "toggle_edge")


class Acon3dFacePanel(bpy.types.Panel):
    bl_idname = "ACON_PT_Face_Main"
    bl_label = "Face Control"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="NODE_MATERIAL")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.scale_x = 3
        col.separator()
        col = row.column()
        row = col.row()
        row.prop(context.scene.ACON_prop, "toggle_texture", text="Texture")
        row = col.row()
        row.prop(context.scene.ACON_prop, "toggle_shading", text="Shading")
        return


class FaceSubPanel(bpy.types.Panel):
    bl_parent_id = "ACON_PT_Face_Main"
    bl_idname = "ACON_PT_Face_sub"
    bl_label = "Toon Style"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene.ACON_prop, "toggle_toon_face", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        if context.scene.ACON_prop.toggle_toon_face:

            prop = context.scene.ACON_prop

            col = layout.column()
            col.prop(prop, "toon_shading_depth")

            if prop.toon_shading_depth == "2":
                col.prop(
                    prop, "toon_shading_brightness_1", text="Brightness", slider=True
                )
            else:
                col.prop(
                    prop, "toon_shading_brightness_1", text="Brightness 1", slider=True
                )
                col.prop(
                    prop, "toon_shading_brightness_2", text="Brightness 2", slider=True
                )


class Acon3dBloomPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""

    bl_parent_id = "ACON_PT_Face_Main"
    bl_idname = "ACON3D_BLOOM_PT_Main"
    bl_label = "Bloom"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"BLENDER_EEVEE"}

    def draw_header(self, context):
        scene = context.scene
        self.layout.prop(scene.ACON_prop, "use_bloom", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        scene = context.scene
        props = scene.eevee

        layout.active = props.use_bloom
        col = layout.column()
        col.prop(props, "bloom_threshold")
        col.prop(props, "bloom_knee")
        col.prop(props, "bloom_radius")
        col.prop(props, "bloom_color")
        col.prop(props, "bloom_intensity")
        col.prop(props, "bloom_clamp")


classes = (
    CloneMaterialOperator,
    Acon3dFacePanel,
    FaceSubPanel,
    Acon3dBloomPanel,
    MATERIAL_UL_List,
    MaterialPanel,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
