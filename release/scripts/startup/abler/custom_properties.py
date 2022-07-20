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


import bpy
from math import radians
from .lib import scenes, cameras, shadow, objects
from .lib.materials import materials_handler


class AconWindowManagerProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.WindowManager.ACON_prop = bpy.props.PointerProperty(
            type=AconWindowManagerProperty
        )

    @classmethod
    def unregister(cls):
        del bpy.types.WindowManager.ACON_prop

    scene: bpy.props.EnumProperty(
        name="Scene",
        description="Change scene",
        items=scenes.add_scene_items,
        update=scenes.load_scene,
    )


class CollectionLayerExcludeProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.l_exclude = bpy.props.CollectionProperty(
            type=CollectionLayerExcludeProperties
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.l_exclude

    def update_layer_visibility(self, context):
        target_layer = bpy.data.collections[self.name]
        for objs in target_layer.objects:
            belonging_col_names = {
                collection.name for collection in objs.users_collection
            }
            should_show = all(
                layer.value
                for layer in bpy.context.scene.l_exclude
                if layer.name in belonging_col_names
            )

            objs.hide_viewport = not should_show
            objs.hide_render = not should_show

    def update_layer_lock(self, context):
        target_layer = bpy.data.collections[self.name]
        for objs in target_layer.objects:
            objs.hide_select = self.lock

    name: bpy.props.StringProperty(name="Layer Name", default="")

    value: bpy.props.BoolProperty(
        name="Layer Exclude",
        description="Make objects on the current layer invisible in the viewport",
        default=True,
        update=update_layer_visibility,
    )

    lock: bpy.props.BoolProperty(
        name="Layer Lock",
        description="Make objects on the current layer lock in the viewport",
        default=False,
        update=update_layer_lock,
    )


class AconSceneSelectedGroupProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.ACON_selected_group = bpy.props.PointerProperty(
            type=AconSceneSelectedGroupProperty
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.ACON_selected_group

    current_root_group: bpy.props.StringProperty(
        name="Current Selected Root Group", default=""
    )
    current_group: bpy.props.StringProperty(name="Current Selected Group", default="")
    direction: bpy.props.EnumProperty(
        name="Level Direction",
        description="Change order of collection level",
        items=[
            ("UP", "up", "Level Up"),
            ("DOWN", "down", "Level Down"),
            ("TOP", "top", "Level Top"),
            ("BOTTOM", "bottom", "Level bottom"),
        ],
    )


class AconSceneProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.ACON_prop = bpy.props.PointerProperty(type=AconSceneProperty)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.ACON_prop

    toggle_toon_edge: bpy.props.BoolProperty(
        # name="Toon Style Edge",
        name="",
        description="Express toon style edge",
        default=True,
        update=materials_handler.toggle_toon_edge,
    )

    edge_min_line_width: bpy.props.FloatProperty(
        # name="Min Line Width",
        name="",
        description="Adjust the thickness of minimum depth edges",
        subtype="PIXEL",
        default=1,
        min=0,
        max=5,
        step=1,
        update=materials_handler.change_line_props,
    )

    edge_max_line_width: bpy.props.FloatProperty(
        # name="Max Line Width",
        name="",
        description="Adjust the thickness of maximum depth edges",
        subtype="PIXEL",
        default=1,
        min=0,
        max=5,
        step=1,
        update=materials_handler.change_line_props,
    )

    edge_line_detail: bpy.props.FloatProperty(
        # name="Line Detail",
        name="",
        description="Amount of edges to be shown. (recommended: 1.2)",
        subtype="FACTOR",
        default=2,
        min=0,
        max=20,
        step=10,
        update=materials_handler.change_line_props,
    )

    toggle_toon_face: bpy.props.BoolProperty(
        # name="Toon Style Face",
        name="",
        description="Express toon style face",
        default=True,
        update=materials_handler.toggle_toon_face,
    )

    toggle_texture: bpy.props.BoolProperty(
        # name="Texture",
        name="",
        description="Express material texture",
        default=True,
        update=materials_handler.toggle_texture,
    )

    toggle_shading: bpy.props.BoolProperty(
        # name="Shading",
        name="",
        description="Express shading",
        default=True,
        update=materials_handler.toggle_shading,
    )

    toon_shading_depth: bpy.props.EnumProperty(
        name="Toon Color Depth",
        description="Change number of colors used for shading",
        items=[("2", "2 depth", ""), ("3", "3 depth", "")],
        default="3",
        update=materials_handler.change_toon_depth,
    )

    toon_shading_brightness_1: bpy.props.FloatProperty(
        # name="Brightness 1",
        name="",
        description="Change shading brightness (Range: 0 ~ 10)",
        subtype="FACTOR",
        default=3,
        min=0,
        max=10,
        step=1,
        update=materials_handler.change_toon_shading_brightness,
    )

    toon_shading_brightness_2: bpy.props.FloatProperty(
        # name="Brightness 2",
        name="",
        description="Change shading brightness (Range: 0 ~ 10)",
        subtype="FACTOR",
        default=5,
        min=0,
        max=10,
        step=1,
        update=materials_handler.change_toon_shading_brightness,
    )

    view: bpy.props.EnumProperty(
        name="View",
        items=cameras.add_view_items_from_collection,
        update=cameras.go_to_custom_camera,
    )

    toggle_sun: bpy.props.BoolProperty(
        # name="Sun Light",
        name="",
        description="Express sunlight",
        default=True,
        update=shadow.toggle_sun,
    )

    sun_strength: bpy.props.FloatProperty(
        # name="Strength",
        name="",
        description="Control the strength of sunlight",
        subtype="FACTOR",
        default=1.5,
        min=0,
        max=10,
        step=1,
        update=shadow.change_sun_strength,
    )

    toggle_shadow: bpy.props.BoolProperty(
        # name="Shadow",
        name="",
        description="Express shadow",
        default=True,
        update=shadow.toggle_shadow,
    )

    sun_rotation_x: bpy.props.FloatProperty(
        # name="Altitude",
        name="",
        description="Adjust sun altitude",
        subtype="ANGLE",
        unit="ROTATION",
        step=100,
        default=radians(20),
        update=shadow.change_sun_rotation,
    )

    sun_rotation_z: bpy.props.FloatProperty(
        # name="Azimuth",
        name="",
        description="Adjust sun azimuth",
        subtype="ANGLE",
        unit="ROTATION",
        step=100,
        default=radians(130),
        update=shadow.change_sun_rotation,
    )

    image_adjust_brightness: bpy.props.FloatProperty(
        # name="Brightness",
        name="",
        description="Adjust the overall brightness (Range: -1 ~ 1)",
        subtype="FACTOR",
        default=0,
        min=-1,
        max=1,
        step=1,
        update=materials_handler.change_image_adjust_brightness,
    )

    image_adjust_contrast: bpy.props.FloatProperty(
        # name="Contrast",
        name="",
        description="Adjust the overall contrast (Range: -1 ~ 1)",
        subtype="FACTOR",
        default=0,
        min=-1,
        max=1,
        step=1,
        update=materials_handler.change_image_adjust_contrast,
    )

    image_adjust_color_r: bpy.props.FloatProperty(
        # name="Red",
        name="",
        description="Adjust color balance (Range: 0 ~ 2)",
        subtype="FACTOR",
        default=1,
        min=0,
        max=2,
        step=1,
        update=materials_handler.change_image_adjust_color,
    )

    image_adjust_color_g: bpy.props.FloatProperty(
        # name="Green",
        name="",
        description="Adjust color balance (Range: 0 ~ 2)",
        subtype="FACTOR",
        default=1,
        min=0,
        max=2,
        step=1,
        update=materials_handler.change_image_adjust_color,
    )

    image_adjust_color_b: bpy.props.FloatProperty(
        # name="Blue",
        name="",
        description="Adjust color balance (Range: 0 ~ 2)",
        subtype="FACTOR",
        default=1,
        min=0,
        max=2,
        step=1,
        update=materials_handler.change_image_adjust_color,
    )

    image_adjust_hue: bpy.props.FloatProperty(
        # name="Hue",
        name="",
        description="Adjust hue (Range: 0 ~ 1)",
        subtype="FACTOR",
        default=0.5,
        min=0,
        max=1,
        step=1,
        update=materials_handler.change_image_adjust_hue,
    )

    image_adjust_saturation: bpy.props.FloatProperty(
        # name="Saturation",
        name="",
        description="Adjust saturation (Range: 0 ~ 2)",
        subtype="FACTOR",
        default=1,
        min=0,
        max=2,
        step=1,
        update=materials_handler.change_image_adjust_saturation,
    )

    selected_objects_str: bpy.props.StringProperty(name="Selected Objects")

    use_dof: bpy.props.BoolProperty(
        # name="Depth of Field",
        name="",
        description="Blur objects at a certain distance using the values set below",
        default=False,
        update=scenes.change_dof,
    )

    show_background_images: bpy.props.BoolProperty(
        # name="Background Images",
        name="",
        description="Add images to the front and rear of the model",
        default=False,
        update=scenes.change_background_images,
    )

    use_bloom: bpy.props.BoolProperty(
        # name="Bloom",
        name="",
        description="Create a shining effect with high luminance pixels",
        default=True,
        update=scenes.change_bloom,
    )

    render_with_background_color: bpy.props.BoolProperty(
        name="",
        default=False,
    )


class AconMaterialProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Material.ACON_prop = bpy.props.PointerProperty(
            type=AconMaterialProperty
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Material.ACON_prop

    type: bpy.props.EnumProperty(
        name="Type",
        description="Material Type",
        items=[
            ("Diffuse", "Diffuse", ""),
            ("Mirror", "Reflection", ""),
            ("Glow", "Emission", ""),
            ("Clear", "Transparent", ""),
        ],
        update=materials_handler.change_material_type,
    )

    toggle_shadow: bpy.props.BoolProperty(
        name="Shadow", default=True, update=materials_handler.toggle_each_shadow
    )

    toggle_shading: bpy.props.BoolProperty(
        name="Shading", default=True, update=materials_handler.toggle_each_shading
    )

    toggle_edge: bpy.props.BoolProperty(
        name="Edges", default=True, update=materials_handler.toggle_each_edge
    )


class AconMeshProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Mesh.ACON_prop = bpy.props.PointerProperty(type=AconMeshProperty)

    @classmethod
    def unregister(cls):
        del bpy.types.Mesh.ACON_prop

    def toggle_show_password(self, context):
        if self.show_password:
            self.password_shown = self.password
        else:
            self.password = self.password_shown

    username: bpy.props.StringProperty(name="Username", description="Username")

    password: bpy.props.StringProperty(
        name="Password", description="Password", subtype="PASSWORD"
    )

    password_shown: bpy.props.StringProperty(
        name="Password", description="Password", subtype="NONE"
    )

    show_password: bpy.props.BoolProperty(
        name="Show Password", default=False, update=toggle_show_password
    )

    # TODO: description 달기
    remember_username: bpy.props.BoolProperty(name="Remember Username", default=True)

    login_status: bpy.props.StringProperty(
        name="Login Status",
        description="Login Status",
    )


class AconObjectGroupProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Group", description="Group", default="")


class AconObjectStateProperty(bpy.types.PropertyGroup):

    location: bpy.props.FloatVectorProperty(
        name="location", description="location", subtype="TRANSLATION", unit="LENGTH"
    )
    rotation_euler: bpy.props.FloatVectorProperty(
        name="rotation", description="rotation", subtype="EULER", unit="ROTATION"
    )
    scale: bpy.props.FloatVectorProperty(name="scale", description="scale")


class AconObjectProperty(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.ACON_prop = bpy.props.PointerProperty(type=AconObjectProperty)

    @classmethod
    def unregister(cls):
        del bpy.types.Object.ACON_prop

    group: bpy.props.CollectionProperty(type=AconObjectGroupProperty)

    group_list: bpy.props.EnumProperty(
        name="View",
        items=objects.add_group_list_from_collection,
    )

    constraint_to_camera_rotation_z: bpy.props.BoolProperty(
        # name="Look at me",
        name="",
        description="Set object to look camera",
        default=False,
        update=objects.toggle_constraint_to_camera,
    )

    use_state: bpy.props.BoolProperty(
        # name="Use State",
        name="",
        description="Move object using the preset state information and the slider below",
        default=False,
        update=objects.toggle_use_state,
    )

    state_exists: bpy.props.BoolProperty(
        name="Determine if state is created", default=False
    )

    state_slider: bpy.props.FloatProperty(
        name="State Slider",
        description="",
        default=0,
        min=0,
        max=1,
        step=1,
        update=objects.move_state,
    )

    state_begin: bpy.props.PointerProperty(type=AconObjectStateProperty)

    state_end: bpy.props.PointerProperty(type=AconObjectStateProperty)


classes = (
    AconWindowManagerProperty,
    CollectionLayerExcludeProperties,
    AconSceneSelectedGroupProperty,
    AconSceneProperty,
    AconMaterialProperty,
    AconMeshProperty,
    AconObjectGroupProperty,
    AconObjectStateProperty,
    AconObjectProperty,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
