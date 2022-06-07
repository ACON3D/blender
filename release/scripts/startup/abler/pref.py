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

    # TODO: Blend -> File Open과 바로 File Open을 할 때 sys.argv의 차이가 있음
    #       이 부분 조작 가능한지 테스트 하는 과정
    print()
    print("*" * 50)
    print(sys.argv)

    if len(sys.argv) == 1:
        print("에이블러만 열었음")

    if len(sys.argv) > 1:
        print("파일도 같이 열었음")

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

    print(" -> pref.save_pre_handler")

    filepath = bpy.data.filepath

    if filepath is (None or ""):
        print(" 빈 파일. 저장하기")
        print("*" * 50)

    else:
        scene_list = [s.name for s in bpy.data.scenes]
        print(f" 저장된 씬 목록: {scene_list}")

        name = bpy.data.window_managers["WinMan"].ACON_prop.scene
        num = scene_list.index(name)
        print(f" 저장할 씬 (이름, 번호): {name, num}")

        print()
        print(" -> ACON_prop.scene_number 업데이트 하기")
        print(" -> scene_number에 접근해서 custom_properties로 넘어감")
        bpy.context.window_manager.ACON_prop.scene_number = num

        print(" -> 업데이트 된 번호 확인")
        print(f" scene_number: {bpy.context.window_manager.ACON_prop.scene_number}")
        print("-> 저장 마무리")
        print("*" * 50)
        print()

    return


@persistent
def save_post_handler(dummy):
    materials_handler.toggleToonEdge(None, None)
    materials_handler.toggleToonFace(None, None)

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
