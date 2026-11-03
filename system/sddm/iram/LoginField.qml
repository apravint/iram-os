// A text field styled from the parent theme's colors.
import QtQuick
import QtQuick.Controls

TextField {
    id: field
    implicitHeight: 46 * root.unit
    color: root.fg
    placeholderTextColor: root.muted
    selectionColor: root.accent
    selectedTextColor: root.color
    font.family: root.fontFamily
    font.pixelSize: 16 * root.unit
    leftPadding: 16 * root.unit
    rightPadding: 16 * root.unit
    background: Rectangle {
        radius: 10 * root.unit
        color: Qt.rgba(0, 0, 0, 0.28)
        border.width: field.activeFocus ? 2 : 1
        border.color: field.activeFocus ? root.accent : Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.18)
    }
}
