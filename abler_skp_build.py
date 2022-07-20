import os
import platform
import shutil

src_path = "./release/scripts/addons_abler/io_skp"
dest_path_ending = "2.96/scripts/addons_abler/io_skp"
dest_path = ""


def copy_scripts(src, dest):
    shutil.copytree(src, dest, dirs_exist_ok=True)


if platform.system() == "Windows":
    dest_path_heading = "../build_windows_x64_vc17_Release/bin/Release/"
    dest_path = os.path.join(dest_path_heading, dest_path_ending)
elif platform.system() == "Darwin":
    dest_path_heading = "../build_darwin/bin/ABLER.app/Contents/Resources/"
    dest_path = os.path.join(dest_path_heading, dest_path_ending)

else:
    print("Not supported")
    exit(1)
try:
    copy_scripts(src_path, dest_path)
    print("Successfully copied scripts from addons_abler/io_skp")
except Exception as e:
    raise e
