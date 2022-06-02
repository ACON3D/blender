import os
import sys
from types import SimpleNamespace

import bpy
from bpy.app.handlers import persistent

from .lib import cameras, shadow, render, scenes, post_open
from .lib.materials import materials_setup, materials_handler
from .lib.tracker import tracker


def init_setting(dummy):
    prefs = bpy.context.preferences
    prefs_sys = prefs.system
    prefs_view = prefs.view
    prefs_paths = prefs.filepaths

    if "--background" not in sys.argv and "-b" not in sys.argv:
        try:
            init_screen = bpy.data.screens["ACON3D"].areas[0].spaces[0]
            init_screen.shading.type = "RENDERED"
            init_screen.show_region_header = False
            init_screen.show_region_tool_header = False
            init_screen.show_gizmo = True
            init_screen.show_gizmo_object_translate = True
            init_screen.show_gizmo_object_rotate = True
            init_screen.show_gizmo_object_scale = True
            init_screen.show_gizmo_navigate = False
            init_screen.show_gizmo_tool = True
            init_screen.show_gizmo_context = True

        except:
            print("Failed to find screen 'ACON3D'")

    prefs_sys.use_region_overlap = False
    prefs_view.show_column_layout = True
    prefs_view.show_navigate_ui = False
    prefs_view.show_developer_ui = False
    prefs_view.show_tooltips_python = False
    prefs_paths.use_load_ui = False

    print("\ninit_setting")
    print(f"filepath : {bpy.data.filepath}")

    if bpy.data.filepath is (None or ""):
        print("에이블러 열고, userpref 불러옴\n")

    else:
        num = bpy.context.scene.ACON_prop.scene_number
        print(f"저장된 scene_number: {num}")

        s_list = []
        for s in bpy.data.scenes:
            s_list.append(s.name)

        print(f"저장된 scene.name: {s_list[num]}")
        print("이제 씬 업데이트를 해야함")

        bpy.data.window_managers["WinMan"].ACON_prop.scene = s_list[num]
        print(f"최종 로드 이름: {bpy.context.scene.name}")



@persistent
def load_handler(dummy):
    tracker.turn_off()
    try:
        init_setting(None)
        cameras.makeSureCameraExists()
        cameras.switchToRendredView()
        cameras.turnOnCameraView(False)
        shadow.setupSharpShadow()
        render.setupBackgroundImagesCompositor()
        materials_setup.applyAconToonStyle()
        for scene in bpy.data.scenes:
            scene.view_settings.view_transform = "Standard"
        # 키맵이 ABLER로 세팅되어있는지 확인하고, 아닐 경우 세팅을 바로잡아줌
        if bpy.context.preferences.keymap.active_keyconfig != "ABLER":
            abler_keymap_path: str = os.path.join(bpy.utils.script_paths()[1], "presets", "keyconfig", "ABLER.py")
            bpy.ops.preferences.keyconfig_activate(filepath=abler_keymap_path)
        scenes.refresh_look_at_me()
        post_open.change_and_reset_value()
        post_open.update_scene()
        post_open.update_layers()
        post_open.hide_adjust_last_operation_panel()

    finally:
        tracker.turn_on()


@persistent
def save_pre_handler(dummy):
    override = SimpleNamespace()
    override_scene = SimpleNamespace()
    override.scene = override_scene
    override_ACON_prop = SimpleNamespace()
    override_scene.ACON_prop = override_ACON_prop
    override_ACON_prop.toggle_toon_edge = False
    override_ACON_prop.toggle_toon_face = False
    materials_handler.toggleToonEdge(None, override)
    materials_handler.toggleToonFace(None, override)

    print("save_pre_handler()")
    print(f"scene_number = {bpy.context.scene.ACON_prop.scene_number}")
    bpy.context.scene.ACON_prop.scene_number = 0


@persistent
def save_post_handler(dummy):
    materials_handler.toggleToonEdge(None, None)
    materials_handler.toggleToonFace(None, None)

    print("save_post_handler()")
    print(f"scene_number = {bpy.context.scene.ACON_prop.scene_number}")
    bpy.context.scene.ACON_prop.scene_number = 2

    for scene in bpy.data.scenes:
        scene.view_settings.view_transform = "Standard"


def register():
    bpy.app.handlers.load_factory_startup_post.append(init_setting)
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)
    bpy.app.handlers.save_post.append(save_post_handler)


def unregister():
    bpy.app.handlers.save_post.remove(save_post_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.load_factory_startup_post.remove(init_setting)
