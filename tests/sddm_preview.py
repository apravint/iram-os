#!/usr/bin/env python3
"""
Renders the IRAM SDDM theme offscreen against a stand-in for SDDM's greeter API,
and fails on any QML warning. Optionally saves screenshots for review.

Usage: sddm_preview.py [--out DIR] [--background IMAGE] [--theme-conf FILE]
Needs PyQt6 with QtQuick. Exits 77 (skip) when it is not installed.
"""

import argparse
import configparser
import os
import sys

try:
    from PyQt6.QtCore import QObject, QSize, QUrl, Qt, QtMsgType, qInstallMessageHandler, pyqtProperty, pyqtSignal, pyqtSlot, QTimer
    from PyQt6.QtGui import QGuiApplication, QStandardItem, QStandardItemModel
    from PyQt6.QtQml import QQmlPropertyMap
    from PyQt6.QtQuick import QQuickView
except ImportError:
    print("PyQt6 with QtQuick is not installed; skipping.")
    sys.exit(77)

THEME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "system", "sddm", "iram")
NAME_ROLE = Qt.ItemDataRole.UserRole + 1


class FakeSddm(QObject):
    """The subset of SDDM's `sddm` context object the theme uses."""
    loginFailed = pyqtSignal()
    loginSucceeded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.calls = []

    @pyqtProperty(bool, constant=True)
    def canPowerOff(self):
        return True

    @pyqtProperty(bool, constant=True)
    def canReboot(self):
        return True

    @pyqtProperty(bool, constant=True)
    def canSuspend(self):
        return True

    @pyqtSlot(str, str, int)
    def login(self, user, password, session):
        self.calls.append(("login", user, password, session))

    @pyqtSlot()
    def powerOff(self):
        self.calls.append(("powerOff",))

    @pyqtSlot()
    def reboot(self):
        self.calls.append(("reboot",))

    @pyqtSlot()
    def suspend(self):
        self.calls.append(("suspend",))


class NamedModel(QStandardItemModel):
    """A list model exposing a `name` role plus SDDM's lastIndex/lastUser properties."""

    def __init__(self, names, last_index, last_user=""):
        super().__init__()
        for name in names:
            item = QStandardItem()
            item.setData(name, NAME_ROLE)
            self.appendRow(item)
        self._last_index = last_index
        self._last_user = last_user

    def roleNames(self):
        return {NAME_ROLE: b"name"}

    @pyqtProperty(int, constant=True)
    def lastIndex(self):
        return self._last_index

    @pyqtProperty(str, constant=True)
    def lastUser(self):
        return self._last_user


def load_config(theme_conf, background):
    parser = configparser.ConfigParser()
    parser.read(os.path.join(THEME_DIR, "theme.conf"))
    if theme_conf:
        parser.read(theme_conf)
    values = dict(parser["General"]) if parser.has_section("General") else {}
    if background:
        values["background"] = os.path.abspath(background)
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    parser.add_argument("--background")
    parser.add_argument("--theme-conf")
    parser.add_argument("--size", default="1920x1080")
    args = parser.parse_args()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication(sys.argv[:1])
    warnings = []

    # Runtime errors (TypeError and the like) reach the message handler, not engine.warnings.
    def on_message(kind, context, message):
        if kind != QtMsgType.QtDebugMsg and ("qml" in message.lower() or "TypeError" in message or ".qml:" in message):
            warnings.append(message)
    qInstallMessageHandler(on_message)

    view = QQuickView()
    view.engine().warnings.connect(lambda errs: warnings.extend(e.toString() for e in errs))
    sddm = FakeSddm()
    config = QQmlPropertyMap()
    for key, value in load_config(args.theme_conf, args.background).items():
        config.insert(key, value)
    sessions = NamedModel(["Plasma (Wayland)", "IRAM OS", "Hyprland"], -1)
    users = NamedModel(["apravint"], 0, "apravint")
    context = view.rootContext()
    context.setContextProperty("sddm", sddm)
    context.setContextProperty("config", config)
    context.setContextProperty("sessionModel", sessions)
    context.setContextProperty("userModel", users)

    width, height = (int(v) for v in args.size.split("x"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    # The offscreen platform's default screen is small; pin the window to the size asked for.
    view.setMinimumSize(QSize(width, height))
    view.setMaximumSize(QSize(width, height))
    view.resize(width, height)
    view.setSource(QUrl.fromLocalFile(os.path.abspath(os.path.join(THEME_DIR, "Main.qml"))))
    if view.status() != QQuickView.Status.Ready:
        for error in view.errors():
            print("QML error:", error.toString())
        return 1
    view.show()

    root = view.rootObject()
    failures = []
    shots = []

    def step(action):
        QTimer.singleShot(0, action)

    def capture(name):
        if args.out:
            os.makedirs(args.out, exist_ok=True)
            path = os.path.join(args.out, f"{name}.png")
            view.grabWindow().save(path)
            shots.append(path)

    def check_session_default():
        # With no history, the theme should offer IRAM OS rather than the first entry.
        combo = root.findChild(QObject, "sessionBox")
        index = combo.property("currentIndex") if combo else None
        if index != 1:
            failures.append(f"default session index is {index}, expected IRAM OS (1)")

    def run():
        capture("login")
        check_session_default()
        sddm.loginFailed.emit()
        QTimer.singleShot(300, after_failure)

    def after_failure():
        capture("login-failed")
        if root.property("statusText") != "Wrong password. Try again.":
            failures.append(f"status after failure: {root.property('statusText')!r}")
        app.quit()

    QTimer.singleShot(400, run)
    app.exec()

    for warning in warnings:
        print("QML warning:", warning)
    for failure in failures:
        print("FAIL:", failure)
    for shot in shots:
        print("saved", shot)
    return 1 if warnings or failures else 0


if __name__ == "__main__":
    sys.exit(main())
