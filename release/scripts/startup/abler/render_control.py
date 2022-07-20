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


import bpy, platform, os, subprocess
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .lib import render, cameras
from .lib.materials import materials_handler
from .lib.tracker import tracker
from bpy.props import StringProperty


bl_info = {
    "name": "ACON3D Panel",
    "description": "",
    "author": "sdk@acon3d.com",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "ACON3D",
}


def open_directory(path):

    if platform.system() == "Windows":

        FILEBROWSER_PATH = os.path.join(os.getenv("WINDIR"), "explorer.exe")
        path = os.path.normpath(path)

        if os.path.isdir(path):
            subprocess.run([FILEBROWSER_PATH, path])
        elif os.path.isfile(path):
            subprocess.run([FILEBROWSER_PATH, "/select,", os.path.normpath(path)])

    elif platform.system() == "Darwin":
        subprocess.call(["open", "-R", path])

    elif platform.system() == "Linux":
        print("Linux")


class Acon3dCameraViewOperator(bpy.types.Operator):
    """Fit render region to viewport"""

    bl_idname = "acon3d.camera_view"
    bl_label = "Camera View"
    bl_translation_context = "*"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cameras.turn_on_camera_view()

        return {"FINISHED"}


class Acon3dRenderOperator(bpy.types.Operator):

    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(default="*.png", options={"HIDDEN"})
    show_on_completion: bpy.props.BoolProperty(
        name="Show in folder on completion", default=True
    )
    write_still = True
    render_queue = []
    rendering = False
    render_canceled = False
    timer_event = None
    initial_scene = None
    initial_display_type = None

    def pre_render(self, dummy, dum):
        self.rendering = True

    def post_render(self, dummy, dum):
        if not self.render_queue:
            self.render_queue.pop(0)
            self.rendering = False

    def on_render_cancel(self, dummy, dum):
        self.render_canceled = True

    def on_render_finish(self, context):
        # set initial_scene
        bpy.data.window_managers["WinMan"].ACON_prop.scene = self.initial_scene.name
        return {"FINISHED"}

    def prepare_queue(self, context):

        for scene in bpy.data.scenes:
            self.render_queue.append(scene)

        return {"RUNNING_MODAL"}

    def prepare_render(self):
        render.setup_background_images_compositor()
        render.match_object_visibility()

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        self.render_canceled = False
        self.rendering = False
        self.render_queue = []
        self.initial_scene = context.scene
        self.initial_display_type = context.preferences.view.render_display_type
        self.timer_event = context.window_manager.event_timer_add(
            0.2, window=context.window
        )

        context.preferences.view.render_display_type = "NONE"
        context.window_manager.modal_handler_add(self)

        bpy.app.handlers.render_pre.append(self.pre_render)
        bpy.app.handlers.render_post.append(self.post_render)
        bpy.app.handlers.render_cancel.append(self.on_render_cancel)

        return self.prepare_queue(context)

    def modal(self, context, event):
        return {"PASS_THROUGH"}


class Acon3dRenderFileOperator(Acon3dRenderOperator, ExportHelper):
    # Render Type : Quick, Full, Line, Shadow

    def __init__(self):
        scene = bpy.context.scene
        self.filepath = f"{scene.name}{self.filename_ext}"

    def execute(self, context):
        # Get basename without file extension
        self.dirname, self.basename = os.path.split(os.path.normpath(self.filepath))

        if "." in self.basename:
            self.basename = ".".join(self.basename.split(".")[:-1])

        return super().execute(context)

    def modal(self, context, event):

        if event.type == "TIMER":

            if not self.render_queue or self.render_canceled is True:

                bpy.app.handlers.render_pre.remove(self.pre_render)
                bpy.app.handlers.render_post.remove(self.post_render)
                bpy.app.handlers.render_cancel.remove(self.on_render_cancel)

                context.window_manager.event_timer_remove(self.timer_event)
                context.window.scene = self.initial_scene
                context.preferences.view.render_display_type = self.initial_display_type

                self.report({"INFO"}, "RENDER QUEUE FINISHED")

                bpy.ops.acon3d.alert(
                    "INVOKE_DEFAULT",
                    title="Render Queue Finished",
                    message_1="Rendered images are saved in:",
                    message_2=self.filepath,
                )

                if self.show_on_completion:
                    open_directory(self.filepath)

                return self.on_render_finish(context)

            elif self.rendering is False:

                qitem = self.render_queue[0]

                # Update filename
                if qitem.name != self.basename:
                    qitem.name = self.basename

                base_filepath = os.path.join(self.dirname, qitem.name)
                file_format = qitem.render.image_settings.file_format
                numbered_filepath = base_filepath
                number = 2

                while os.path.isfile(f"{numbered_filepath}.{file_format}"):
                    numbered_filepath = f"{base_filepath} ({number})"
                    number += 1

                qitem.render.filepath = numbered_filepath
                self.filepath = f"{numbered_filepath}{self.filename_ext}"
                context.window_manager.ACON_prop.scene = qitem.name

                self.prepare_render()

                bpy.ops.render.render("INVOKE_DEFAULT", write_still=self.write_still)

        return {"PASS_THROUGH"}


class Acon3dRenderDirOperator(Acon3dRenderOperator, ImportHelper):
    # Render Type : All Scene, Snip

    def __init__(self):
        # Get basename without file extension
        self.filepath = bpy.context.blend_data.filepath

        if not self.filepath:
            self.filepath = "untitled"

        else:
            self.dirname, self.basename = os.path.split(os.path.normpath(self.filepath))

            if "." in self.basename:
                self.basename = ".".join(self.basename.split(".")[:-1])

            self.filepath = self.basename

    def modal(self, context, event):

        if event.type == "TIMER":

            if not self.render_queue or self.render_canceled is True:

                bpy.app.handlers.render_pre.remove(self.pre_render)
                bpy.app.handlers.render_post.remove(self.post_render)
                bpy.app.handlers.render_cancel.remove(self.on_render_cancel)

                context.window_manager.event_timer_remove(self.timer_event)
                context.window.scene = self.initial_scene
                context.preferences.view.render_display_type = self.initial_display_type

                self.report({"INFO"}, "RENDER QUEUE FINISHED")

                bpy.ops.acon3d.alert(
                    "INVOKE_DEFAULT",
                    title="Render Queue Finished",
                    message_1="Rendered images are saved in:",
                    message_2=self.filepath,
                )

                if self.show_on_completion:
                    open_directory(self.filepath)

                return self.on_render_finish(context)

            elif self.rendering is False:

                qitem = self.render_queue[0]

                base_filepath = os.path.join(self.filepath, qitem.name)
                file_format = qitem.render.image_settings.file_format
                numbered_filepath = base_filepath
                number = 2
                while os.path.isfile(f"{numbered_filepath}.{file_format}"):
                    numbered_filepath = f"{base_filepath} ({number})"
                    number += 1

                qitem.render.filepath = numbered_filepath
                context.window_manager.ACON_prop.scene = qitem.name

                self.prepare_render()

                bpy.ops.render.render("INVOKE_DEFAULT", write_still=self.write_still)

        return {"PASS_THROUGH"}


class Acon3dRenderAllOperator(Acon3dRenderDirOperator):
    """Render all scenes with full render settings"""

    bl_idname = "acon3d.render_all"
    bl_label = "Save"
    bl_translation_context = "*"

    def prepare_queue(self, context):
        tracker.render_all_scenes()

        super().prepare_queue(context)
        return {"RUNNING_MODAL"}


class Acon3dRenderFullOperator(Acon3dRenderFileOperator):
    """Render according to the set pixel"""

    bl_idname = "acon3d.render_full"
    bl_label = "Full Render"
    bl_translation_context = "*"

    def __init__(self):
        super().__init__()

    def prepare_queue(self, context):
        tracker.render_full()

        self.render_queue.append(context.scene)
        return {"RUNNING_MODAL"}


class Acon3dRenderTempSceneFileOperator(Acon3dRenderFileOperator):

    temp_scenes = []

    def prepare_render(self):
        render.clear_compositor()
        render.match_object_visibility()

    def prepare_queue(self, context):

        scene = context.scene.copy()
        self.render_queue.append(scene)
        self.temp_scenes.append(scene)

        scene.eevee.use_bloom = False
        scene.render.use_lock_interface = True

        for mat in bpy.data.materials:
            mat.blend_method = "OPAQUE"
            mat.shadow_method = "OPAQUE"
            if toonNode := mat.node_tree.nodes.get("ACON_nodeGroup_combinedToon"):
                toonNode.inputs[1].default_value = 0
                toonNode.inputs[3].default_value = 1

        return {"RUNNING_MODAL"}

    def on_render_finish(self, context):

        for mat in bpy.data.materials:
            materials_handler.set_material_parameters_by_type(mat)

        for scene in self.temp_scenes:
            bpy.data.scenes.remove(scene)

        self.temp_scenes.clear()

        # set initial_scene
        bpy.data.window_managers["WinMan"].ACON_prop.scene = self.initial_scene.name

        return {"FINISHED"}


class Acon3dRenderTempSceneDirOperator(Acon3dRenderDirOperator):

    temp_scenes = []

    def prepare_render(self):
        render.clear_compositor()
        render.match_object_visibility()

    def prepare_queue(self, context):

        scene = context.scene.copy()
        self.render_queue.append(scene)
        self.temp_scenes.append(scene)

        scene.eevee.use_bloom = False
        scene.render.use_lock_interface = True

        for mat in bpy.data.materials:
            mat.blend_method = "OPAQUE"
            mat.shadow_method = "OPAQUE"
            if toonNode := mat.node_tree.nodes.get("ACON_nodeGroup_combinedToon"):
                toonNode.inputs[1].default_value = 0
                toonNode.inputs[3].default_value = 1

        return {"RUNNING_MODAL"}

    def on_render_finish(self, context):

        for mat in bpy.data.materials:
            materials_handler.set_material_parameters_by_type(mat)

        for scene in self.temp_scenes:
            bpy.data.scenes.remove(scene)

        self.temp_scenes.clear()

        # set initial_scene
        bpy.data.window_managers["WinMan"].ACON_prop.scene = self.initial_scene.name

        return {"FINISHED"}


class Acon3dRenderShadowOperator(Acon3dRenderTempSceneFileOperator):
    """Renders only shadow according to the set pixel"""

    bl_idname = "acon3d.render_shadow"
    bl_label = "Shadow Render"
    bl_translation_context = "*"

    def __init__(self):
        scene = bpy.context.scene
        self.filepath = f"{scene.name}_shadow{self.filename_ext}"

    def prepare_queue(self, context):
        tracker.render_shadow()

        super().prepare_queue(context)

        scene = self.render_queue[0]
        scene.name = f"{context.scene.name}_shadow"
        prop = scene.ACON_prop
        prop.toggle_texture = False
        prop.toggle_shading = True
        prop.toggle_toon_edge = False

        return {"RUNNING_MODAL"}


class Acon3dRenderLineOperator(Acon3dRenderTempSceneFileOperator):
    """Renders only lines according to the set pixel"""

    bl_idname = "acon3d.render_line"
    bl_label = "Line Render"
    bl_translation_context = "*"

    def __init__(self):
        scene = bpy.context.scene
        self.filepath = f"{scene.name}_line{self.filename_ext}"

    def prepare_queue(self, context):
        tracker.render_line()

        super().prepare_queue(context)

        scene = self.render_queue[0]
        scene.name = f"{context.scene.name}_line"
        prop = scene.ACON_prop
        prop.toggle_texture = False
        prop.toggle_shading = False
        prop.toggle_toon_edge = True

        return {"RUNNING_MODAL"}


class Acon3dRenderSnipOperator(Acon3dRenderTempSceneDirOperator):
    """Render selected objects isolatedly from background"""

    bl_idname = "acon3d.render_snip"
    bl_label = "Snip Render"
    bl_translation_context = "*"

    temp_layer = None
    temp_col = None
    temp_image = None

    @classmethod
    def poll(self, context):
        return len(context.selected_objects)

    def prepare_render(self):

        if len(self.render_queue) == 3:

            render.clear_compositor()

        elif len(self.render_queue) == 2:

            shade_scene = self.temp_scenes[0]
            filename = (
                f"{shade_scene.name}.{shade_scene.render.image_settings.file_format}"
            )

            image_path = os.path.join(self.filepath, filename)
            self.temp_image = bpy.data.images.load(image_path)

            for mat in bpy.data.materials:
                materials_handler.set_material_parameters_by_type(mat)

            compNodes = render.clear_compositor()
            render.setup_background_images_compositor(*compNodes)
            render.setup_snip_compositor(
                *compNodes, snip_layer=self.temp_layer, shade_image=self.temp_image
            )

            os.remove(image_path)

        else:

            bpy.data.collections.remove(self.temp_col)
            bpy.data.images.remove(self.temp_image)
            render.setup_background_images_compositor()

        render.match_object_visibility()

    def prepare_queue(self, context):
        tracker.render_snip()

        super().prepare_queue(context)

        scene = context.scene.copy()
        scene.name = f"{context.scene.name}_snipped"
        self.render_queue.append(scene)
        self.temp_scenes.append(scene)

        layer = scene.view_layers.new("ACON_layer_snip")
        self.temp_layer = layer
        for col in layer.layer_collection.children:
            col.exclude = True

        col_group = bpy.data.collections.new("ACON_group_snip")
        self.temp_col = col_group
        scene.collection.children.link(col_group)
        for obj in context.selected_objects:
            col_group.objects.link(obj)

        scene = context.scene.copy()
        scene.name = f"{context.scene.name}_full"
        self.render_queue.append(scene)
        self.temp_scenes.append(scene)

        return {"RUNNING_MODAL"}


class Acon3dRenderQuickOperator(Acon3dRenderFileOperator):
    """Take a snapshot of the active viewport"""

    bl_idname = "acon3d.render_quick"
    bl_label = "Quick Render"
    bl_translation_context = "*"

    def __init__(self):
        super().__init__()

    def execute(self, context):
        tracker.render_quick()
        return super().execute(context)

    def prepare_queue(self, context):
        render.renderWithWorldBackgroundColor()
        # File name duplicate check

        base_filepath = os.path.join(self.dirname, self.basename)
        file_format = self.filename_ext
        numbered_filepath = base_filepath
        number = 2

        while os.path.isfile(f"{numbered_filepath}{file_format}"):
            numbered_filepath = f"{base_filepath} ({number})"
            number += 1

        context.scene.render.filepath = numbered_filepath
        self.filepath = f"{numbered_filepath}{file_format}"

        for obj in context.selected_objects:
            obj.select_set(False)

        bpy.ops.render.opengl("INVOKE_DEFAULT", write_still=True)

        return {"RUNNING_MODAL"}


class Acon3dRenderPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""

    bl_idname = "ACON3D_PT_render"
    bl_label = "Render"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"BLENDER_RENDER", "BLENDER_EEVEE", "BLENDER_WORKBENCH"}

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="RENDER_STILL")

    def draw(self, context):
        scene = context.scene

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        row = layout.row(align=True)
        row.operator("acon3d.camera_view", text="", icon="RESTRICT_VIEW_OFF")
        row.prop(scene.render, "resolution_x", text="")
        row.prop(scene.render, "resolution_y", text="")

        row = layout.row()
        row.operator("acon3d.render_quick", text="Quick Render", text_ctxt="*")

        if any(obj.type == "CAMERA" for obj in bpy.data.objects):
            row.operator("acon3d.render_full", text="Full Render")
            row = layout.row()
            row.operator("acon3d.render_line", text="Line Render")
            row.operator("acon3d.render_shadow", text="Shadow Render")
            row = layout.row()
            row.operator("acon3d.render_all", text="Render All Scenes")
            row.operator("acon3d.render_snip", text="Snip Render")

        layout = self.layout
        layout.use_property_split = False
        row = layout.row(align=True)
        row.prop(
            scene.ACON_prop,
            "render_with_background_color",
            text="render with background color",
        )


classes = (
    Acon3dCameraViewOperator,
    Acon3dRenderFullOperator,
    Acon3dRenderAllOperator,
    Acon3dRenderShadowOperator,
    Acon3dRenderLineOperator,
    Acon3dRenderSnipOperator,
    Acon3dRenderQuickOperator,
    Acon3dRenderPanel,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
