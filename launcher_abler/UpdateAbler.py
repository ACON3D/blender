import privilege_helper
import pathlib
from PySide2 import QtWidgets, QtCore, QtGui
import qdarkstyle
import mainwindow
import requests
import configparser
import logging
import os
import os.path
import platform
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import time
from distutils.dir_util import copy_tree
from distutils.version import StrictVersion
from typing import Optional

if sys.platform == "win32":
    from win32com.client import Dispatch

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def get_datadir() -> pathlib.Path:
    """
    Returns a parent directory path
    where persistent application data can be stored.

    linux: ~/.local/share
    macOS: ~/Library/Application Support
    windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming/Blender Foundation"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"



appversion = "1.9.8"
dir_ = ""
if sys.platform == "darwin":
    dir_ = "/Applications"

elif sys.platform == "win32":
    dir_ = "C:/Program Files (x86)/ABLER"
launcherdir_ = get_datadir() / "Blender/2.96/updater"
config = configparser.ConfigParser()
btn = {}
lastversion = ""
installedversion = ""
launcher_installed = ""
LOG_FORMAT = (
    "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
)
test_arg = len(sys.argv) > 1 and sys.argv[1] == "--test"
if not os.path.isdir(get_datadir() / "Blender/2.96"):
    os.mkdir(get_datadir() / "Blender/2.96")
if not os.path.isdir(get_datadir() / "Blender/2.96/updater"):
    os.mkdir(get_datadir() / "Blender/2.96/updater")
logging.basicConfig(
    filename=get_datadir() / "Blender/2.96/updater/AblerLauncher.log",
    format=LOG_FORMAT,
    level=logging.DEBUG,
    filemode="w",
)

logger = logging.getLogger()

def check_abler(installedversion)->None:
    # 최신 릴리즈가 있는지 URL 주소로 확인
    finallist = None
    results = []
    url = "https://api.github.com/repos/acon3d/blender/releases/latest"
    if test_arg:
        url = "https://api.github.com/repos/acon3d/blender/releases"
    # TODO: 새 arg 받아서 테스트 레포 url 업데이트

    is_release, req, state_ui = get_req_from_url(url)
    if state_ui:
        return state_ui, finallist

    if not is_release:
        state_ui = "no release"
        return state_ui, finallist
        
    get_results_from_req(req, results)

    if results:
        if installedversion is None or installedversion == "":
            installedversion = "0.0.0"

        # ABLER 릴리즈 버전 > 설치 버전
        if StrictVersion(results[0]["version"]) > StrictVersion(installedversion):
            state_ui = "update ABLER"
            finallist = results
            return state_ui, finallist

        # ABLER 릴리즈 버전 == 설치 버전
        else:
            state_ui = "execute"

    # 통신 오류로 results가 없어서 바로 ABLER 실행
    else:
        state_ui = "execute"

    return state_ui, finallist

def get_req_from_url(dir_name, url):
    # 깃헙 서버에서 url의 릴리즈 정보를 받아오는 함수
    global dir_
    global launcherdir_
    global launcher_installed

    # Do path settings save here, in case user has manually edited it
    global config
    config.read(get_datadir() / "Blender/2.96/updater/config.ini")

    if dir_name == launcherdir_:
        launcher_installed = config.get("main", "launcher")

    config.set("main", "path", dir_)
    with open(get_datadir() / "Blender/2.96/updater/config.ini", "w") as f:
        config.write(f)
    f.close()

    try:
        req = requests.get(url).json()
    except Exception as e:
        # self.statusBar().showMessage(
        #     "Error reaching server - check your internet connection"
        # )
        # logger.error(e)
        # self.frm_start.show()
        logger.error(e)
        state_ui = "error"

    if test_arg:
        req = req[0]

    is_release = True
    try:
        is_release = req["message"] != "Not Found"
    except Exception as e:
        logger.debug("Release found")

    return is_release, req, state_ui

def get_results_from_req(req, results):
    # req에서 필요한 info를 results에 추가
    for asset in req["assets"]:
        target = asset["browser_download_url"]
        filename = target.split("/")[-1]
        target_type = "Release"
        version_tag = req["name"][1:]

        if sys.platform == "win32":
            if (
                "Windows" in target
                and "zip" in target
                and target_type in target
            ):
                info = {
                    "url": target,
                    "os": "Windows",
                    "filename": filename,
                    "version": version_tag,
                    "arch": "x64",
                }
                results.append(info)

        elif sys.platform == "darwin":
            if os.system("sysctl -in sysctl.proc_translated") == 1:
                if (
                    "macOS" in target
                    and "zip" in target
                    and target_type in target
                    and "M1" in target
                ):
                    info = {
                        "url": target,
                        "os": "macOS",
                        "filename": filename,
                        "version": version_tag,
                        "arch": "arm64",
                    }
                    results.append(info)
            else:
                if (
                    "macOS" in target
                    and "zip" in target
                    and target_type in target
                    and "Intel" in target
                ):
                    info = {
                        "url": target,
                        "os": "macOS",
                        "filename": filename,
                        "version": version_tag,
                        "arch": "x86_64",
                    }
                    results.append(info)
