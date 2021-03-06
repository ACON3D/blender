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
import os

from datetime import datetime, timedelta
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .lib import scenes
from .lib.materials import materials_setup
from .lib.tracker import tracker
from .lib.read_cookies import read_remembered_show_guide


def split_filepath(filepath):
    # Get basename without file extension
    dirname, basename = os.path.split(os.path.normpath(filepath))

    if "." in basename:
        basename = ".".join(basename.split(".")[:-1])

    return dirname, basename


def numbering_filepath(filepath, ext):
    dirname, basename = split_filepath(filepath)
    basepath = os.path.join(dirname, basename)

    num_path = basepath
    num_name = basename
    number = 2

    while os.path.isfile(f"{num_path}{ext}"):
        num_path = f"{basepath} ({number})"
        num_name = f"{basename} ({number})"
        number += 1

    return num_path, num_name


class AconTutorialGuidePopUpOperator(bpy.types.Operator):
    """Show Tutorial Guide"""

    bl_idname = "acon3d.tutorial_guide_popup"
    bl_label = "Show Tutorial Guide"
    bl_translation_context = "*"

    def execute(self, context):
        userInfo = bpy.data.meshes.get("ACON_userInfo")
        prop = userInfo.ACON_prop
        prop.show_guide = read_remembered_show_guide()

        bpy.ops.wm.splash_tutorial_1("INVOKE_DEFAULT")
        return {"FINISHED"}


class AconTutorialGuideCloseOperator(bpy.types.Operator):
    """Close Tutorial Guide"""

    bl_idname = "acon3d.tutorial_guide_close"
    bl_label = "OK"

    def execute(self, context):
        bpy.ops.wm.splash_tutorial_close("INVOKE_DEFAULT")
        return {"CANCELLED"}


class AconTutorialGuide1Operator(bpy.types.Operator):
    """Mouse Mode"""

    bl_idname = "acon3d.tutorial_guide_1"
    bl_label = "Mouse Mode"
    bl_translation_context = "*"

    def execute(self, context):
        bpy.ops.acon3d.tutorial_guide_close()
        bpy.ops.wm.splash_tutorial_1("INVOKE_DEFAULT")
        return {"FINISHED"}


class AconTutorialGuide2Operator(bpy.types.Operator):
    """Fly Mode"""

    bl_idname = "acon3d.tutorial_guide_2"
    bl_label = "Fly Mode"
    bl_translation_context = "*"

    def execute(self, context):
        bpy.ops.acon3d.tutorial_guide_close()
        bpy.ops.wm.splash_tutorial_2("INVOKE_DEFAULT")
        return {"FINISHED"}


class AconTutorialGuide3Operator(bpy.types.Operator):
    """Scene Control"""

    bl_idname = "acon3d.tutorial_guide_3"
    bl_label = "Scene Control"
    bl_translation_context = "*"

    def execute(self, context):
        bpy.ops.acon3d.tutorial_guide_close()
        bpy.ops.wm.splash_tutorial_3("INVOKE_DEFAULT")
        return {"FINISHED"}


class ImportOperator(bpy.types.Operator, ImportHelper):
    """Import file according to the current settings"""

    bl_idname = "acon3d.import_blend"
    bl_label = "Import"
    bl_translation_context = "*"

    filter_glob: bpy.props.StringProperty(default="*.blend", options={"HIDDEN"})

    def execute(self, context):
        try:
            for obj in bpy.data.objects:
                obj.select_set(False)

            FILEPATH = self.filepath

            col_layers = bpy.data.collections.get("Layers")
            if not col_layers:
                col_layers = bpy.data.collections.new("Layers")
                context.scene.collection.children.link(col_layers)

            with bpy.data.libraries.load(FILEPATH) as (data_from, data_to):
                data_to.collections = data_from.collections
                data_to.objects = list(data_from.objects)

            children_names = {}

            for coll in data_to.collections:
                for child in coll.children.keys():
                    children_names[child] = True

            for coll in data_to.collections:

                if "ACON_col" in coll.name:
                    data_to.collections.remove(coll)
                    break

                found = any(coll.name == child for child in children_names)
                if coll.name == "Layers" or (
                    "Layers." in coll.name and len(coll.name) == 10
                ):
                    for coll_2 in coll.children:
                        added_l_exclude = context.scene.l_exclude.add()
                        added_l_exclude.name = coll_2.name
                        added_l_exclude.value = True
                        col_layers.children.link(coll_2)

            for obj in data_to.objects:
                if obj.type == "MESH":
                    obj.select_set(True)
                else:
                    data_to.objects.remove(obj)

            materials_setup.apply_ACON_toon_style()

            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    ctx = bpy.context.copy()
                    ctx["area"] = area
                    ctx["region"] = area.regions[-1]
                    bpy.ops.view3d.view_selected(ctx)

        except Exception as e:
            tracker.import_blend_fail()
            raise e
        else:
            tracker.import_blend()

        return {"FINISHED"}


class ToggleToolbarOperator(bpy.types.Operator):
    """Toggle toolbar visibility"""

    bl_idname = "acon3d.context_toggle"
    bl_label = "Toggle Toolbar"
    bl_translation_context = "*"

    def execute(self, context):
        tracker.toggle_toolbar()

        context.scene.render.engine = "BLENDER_EEVEE"
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        value = space.show_region_toolbar
                        space.show_region_toolbar = not value

        return {"FINISHED"}


class BaseFileOpenOperator:
    filepath: bpy.props.StringProperty(name="text", default="")

    def open_file(self):
        try:
            path = self.filepath

            if path.endswith("/") or path.endswith("\\") or path.endswith("//"):
                return
            elif not os.path.isfile(path):
                bpy.ops.acon3d.alert(
                    "INVOKE_DEFAULT",
                    title="File not found",
                    message_1="Selected file does not exist",
                )
                tracker.file_open_fail()
                return

            bpy.ops.wm.open_mainfile(
                "INVOKE_DEFAULT", filepath=path, display_file_selector=False
            )

        except:
            tracker.file_open_fail()
        else:
            tracker.file_open()


class FileOpenOperator(bpy.types.Operator, ImportHelper, BaseFileOpenOperator):
    """Open new file"""

    bl_idname = "acon3d.file_open"
    bl_label = "File Open"
    bl_translation_context = "*"

    filter_glob: bpy.props.StringProperty(default="*.blend", options={"HIDDEN"})

    def execute(self, context):
        self.open_file()
        return {"FINISHED"}


class FileRecentOpenOperator(bpy.types.Operator, BaseFileOpenOperator):
    bl_idname = "acon3d.recent_file_open"
    bl_label = ""
    bl_translation_context = "*"

    @classmethod
    def description(cls, context, properties):
        filepath = properties.filepath

        if not os.path.isfile(filepath):
            return f"{filepath}\n\nFile Not Found"

        modified_datetime = datetime.fromtimestamp(os.path.getmtime(filepath))
        time_distance = datetime.today().date() - modified_datetime.date()

        if time_distance == timedelta():
            modified_time = modified_datetime.strftime("Today %H:%M")
        elif time_distance == timedelta(days=1):
            modified_time = modified_datetime.strftime("Yesterday %H:%M")
        else:
            modified_time = modified_datetime.strftime("%d %b %Y %H:%M")

        modified_time = f"Modified: {modified_time}"

        size = round(os.path.getsize(filepath) / 1000000.0, 1)
        size = f"Size: {size} MB"

        return f"{filepath}\n\n{modified_time}\n{size}"

    def execute(self, context):
        self.open_file()
        return {"FINISHED"}


class FlyOperator(bpy.types.Operator):
    """Move around the scene using WASD, QE, and mouse like FPS game"""

    bl_idname = "acon3d.fly_mode"
    bl_label = "Fly Mode (shift + `)"
    bl_translation_context = "*"

    def execute(self, context):
        tracker.fly_mode()

        if context.space_data.type == "VIEW_3D":
            bpy.ops.view3d.walk("INVOKE_DEFAULT")

        return {"FINISHED"}


class SaveOperator(bpy.types.Operator, ExportHelper):
    """Save the current Blender file"""

    bl_idname = "acon3d.save"
    bl_label = "Save"
    bl_translation_context = "*"

    filename_ext = ".blend"

    # invoke() ????????? ?????? ?????? execute() ?????? ?????? ????????? ?????? ???????????????.
    # Helper ??????????????? invoke()??? ??????????????? ?????? ???????????? ????????? ?????????,
    # ????????? ?????? ????????? ?????? invoke()??? ???????????? ?????? ?????????????????? ???????????? ????????? ???????????????,
    # ????????? ?????? ????????? ????????? ?????? invoke()??? ???????????? ?????? execute()??? ???????????? ?????????.
    def invoke(self, context, event):
        if bpy.data.is_saved:
            return self.execute(context)

        else:
            return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        try:
            if bpy.data.is_saved:
                self.filepath = context.blend_data.filepath
                dirname, basename = split_filepath(self.filepath)

                bpy.ops.wm.save_mainfile({"dict": "override"}, filepath=self.filepath)
                self.report({"INFO"}, f'Saved "{basename}{self.filename_ext}"')

            else:
                numbered_filepath, numbered_filename = numbering_filepath(
                    self.filepath, self.filename_ext
                )

                self.filepath = f"{numbered_filepath}{self.filename_ext}"

                bpy.ops.wm.save_mainfile({"dict": "override"}, filepath=self.filepath)
                self.report({"INFO"}, f'Saved "{numbered_filename}{self.filename_ext}"')

        except Exception as e:
            tracker.save_fail()
            raise e
        else:
            tracker.save()

        return {"FINISHED"}


class SaveAsOperator(bpy.types.Operator, ExportHelper):
    """Save the current file in the desired location"""

    bl_idname = "acon3d.save_as"
    bl_label = "Save As"
    bl_translation_context = "*"

    filename_ext = ".blend"

    def execute(self, context):
        try:
            numbered_filepath, numbered_filename = numbering_filepath(
                self.filepath, self.filename_ext
            )

            self.filepath = f"{numbered_filepath}{self.filename_ext}"

            bpy.ops.wm.save_as_mainfile({"dict": "override"}, filepath=self.filepath)
            self.report({"INFO"}, f'Saved "{numbered_filename}{self.filename_ext}"')

        except Exception as e:
            tracker.save_as_fail()
            raise e
        else:
            tracker.save_as()

        return {"FINISHED"}


class Acon3dImportPanel(bpy.types.Panel):
    bl_idname = "ACON3D_PT_import"
    bl_label = "General"
    bl_category = "ACON3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="EVENT_A")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.0
        row.operator("acon3d.tutorial_guide_popup")

        row = layout.row()
        row.scale_y = 1.0
        row.operator("acon3d.file_open")
        row.operator("acon3d.import_blend", text="Import")

        row = layout.row()
        row.scale_y = 1.0
        row.operator("acon3d.save", text="Save")
        row.operator("acon3d.save_as", text="Save As...")

        row = layout.row()
        prefs = context.preferences
        view = prefs.view

        row.prop(view, "language")
        row = layout.row()
        row.operator("acon3d.context_toggle")
        row = layout.row()
        row.operator("acon3d.fly_mode")


class ApplyToonStyleOperator(bpy.types.Operator):
    """Apply Toon Style"""

    bl_idname = "acon3d.apply_toon_style"
    bl_label = "Apply Toon Style"
    bl_translation_context = "*"

    def execute(self, context):
        materials_setup.apply_ACON_toon_style()
        scenes.load_scene(None, None)

        return {"FINISHED"}


classes = (
    AconTutorialGuidePopUpOperator,
    AconTutorialGuideCloseOperator,
    AconTutorialGuide1Operator,
    AconTutorialGuide2Operator,
    AconTutorialGuide3Operator,
    Acon3dImportPanel,
    ToggleToolbarOperator,
    ImportOperator,
    ApplyToonStyleOperator,
    FileOpenOperator,
    FileRecentOpenOperator,
    FlyOperator,
    SaveOperator,
    SaveAsOperator,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
