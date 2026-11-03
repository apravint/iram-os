// IRAM OS login screen for SDDM (Qt 6, Theme API 2.0).
// Colors and wallpaper come from theme.conf.user, which iram-sddm-theme-sync writes
// from the active IRAM theme, so the login screen matches the desktop it opens.

import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Layouts

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: config.background_color || "#16161e"

    readonly property color fg: config.foreground || "#c0caf5"
    readonly property color muted: config.muted || "#565f89"
    readonly property color accent: config.accent || "#7aa2f7"
    readonly property color accent2: config.accent_secondary || accent
    readonly property color errorColor: config.error || "#f7768e"
    readonly property string fontFamily: config.font || "JetBrainsMono Nerd Font"
    // The card scales with the screen, so it reads the same on a laptop and a 4K monitor.
    readonly property real unit: Math.max(1, Math.min(width / 1920, height / 1080))
    property string statusText: ""
    // Read SDDM's capabilities here, in the root scope: the power delegates below
    // cannot reach the `sddm` context object while they are being created.
    readonly property bool canSuspend: sddm.canSuspend
    readonly property bool canReboot: sddm.canReboot
    readonly property bool canPowerOff: sddm.canPowerOff

    function power(action) {
        if (action === "suspend") sddm.suspend()
        else if (action === "reboot") sddm.reboot()
        else if (action === "powerOff") sddm.powerOff()
    }

    function attemptLogin() {
        if (password.text.length === 0 || username.text.length === 0)
            return
        statusText = "Signing in…"
        sddm.login(username.text, password.text, session.currentIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.statusText = "Wrong password. Try again."
            password.text = ""
            password.forceActiveFocus()
            shake.start()
        }
        function onLoginSucceeded() {
            root.statusText = ""
        }
    }

    // ---- Background: the theme's wallpaper, or a gradient in its colors -------------
    Image {
        id: wallpaper
        anchors.fill: parent
        source: config.background ? "file://" + config.background : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        visible: status === Image.Ready
    }
    Rectangle {
        anchors.fill: parent
        visible: !wallpaper.visible
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: Qt.darker(root.accent, 3.2) }
            GradientStop { position: 1.0; color: root.color }
        }
    }
    // Darken toward the bottom-left, where the clock sits, so it stays legible on bright art.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.0) }
            GradientStop { position: 0.5; color: Qt.rgba(0, 0, 0, 0.08) }
            GradientStop { position: 0.75; color: Qt.rgba(0, 0, 0, 0.28) }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.55) }
        }
    }

    // Fine grain over every gradient. At 8 bits per channel a long, dark gradient has too
    // few shades and shows visible steps; noise dithers them away without being noticeable.
    Image {
        anchors.fill: parent
        source: "noise.png"
        fillMode: Image.Tile
        opacity: 0.035
        smooth: false
    }

    // ---- Brand and clock, bottom left --------------------------------------------------
    ColumnLayout {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 72 * root.unit
        spacing: 4 * root.unit

        RowLayout {
            spacing: 14 * root.unit
            Image {
                source: "logo.svg"
                sourceSize: Qt.size(40 * root.unit, 40 * root.unit)
                Layout.preferredWidth: 40 * root.unit
                Layout.preferredHeight: 40 * root.unit
            }
            Text {
                text: "IRAM OS"
                color: "white"
                font.family: root.fontFamily
                font.pixelSize: 22 * root.unit
                font.weight: Font.Bold
                font.letterSpacing: 4 * root.unit
            }
        }
        Text {
            id: clock
            color: "white"
            font.family: root.fontFamily
            font.pixelSize: 96 * root.unit
            font.weight: Font.Light
            text: Qt.formatTime(new Date(), "HH:mm")
        }
        Text {
            id: date
            color: Qt.rgba(1, 1, 1, 0.8)
            font.family: root.fontFamily
            font.pixelSize: 22 * root.unit
            text: Qt.formatDate(new Date(), "dddd, d MMMM")
        }
        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: {
                var now = new Date()
                clock.text = Qt.formatTime(now, "HH:mm")
                date.text = Qt.formatDate(now, "dddd, d MMMM")
            }
        }
    }

    // ---- Login card, centered -----------------------------------------------------------
    Item {
        id: card
        width: 420 * root.unit
        height: content.implicitHeight + 64 * root.unit
        anchors.centerIn: parent

        // Frosted glass: a blurred copy of the wallpaper region behind the card.
        ShaderEffectSource {
            id: behind
            sourceItem: wallpaper
            sourceRect: Qt.rect(card.x, card.y, card.width, card.height)
            visible: false
        }
        // Blur first, then clip the result to the card's rounded shape.
        Item {
            anchors.fill: parent
            visible: wallpaper.visible
            layer.enabled: true
            layer.effect: MultiEffect {
                maskEnabled: true
                maskSource: cardMask
            }
            MultiEffect {
                anchors.fill: parent
                source: behind
                autoPaddingEnabled: false
                blurEnabled: true
                blur: 1.0
                blurMax: 64
            }
        }
        Rectangle {
            id: cardMask
            anchors.fill: parent
            radius: 18 * root.unit
            visible: false
            layer.enabled: true
        }
        Rectangle {
            anchors.fill: parent
            radius: 18 * root.unit
            color: Qt.rgba(root.color.r, root.color.g, root.color.b, 0.62)
            border.width: 1
            border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.45)
        }

        ColumnLayout {
            id: content
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 32 * root.unit
            spacing: 14 * root.unit

            // Avatar: the user's initial in the theme's gradient.
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 84 * root.unit
                height: width
                radius: width / 2
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: root.accent }
                    GradientStop { position: 1.0; color: root.accent2 }
                }
                Text {
                    anchors.centerIn: parent
                    text: (username.text || "?").charAt(0).toUpperCase()
                    color: root.color
                    font.family: root.fontFamily
                    font.pixelSize: 38 * root.unit
                    font.weight: Font.Bold
                }
            }

            LoginField {
                id: username
                Layout.fillWidth: true
                placeholderText: "Username"
                text: userModel.lastUser
                onAccepted: password.forceActiveFocus()
            }
            LoginField {
                id: password
                Layout.fillWidth: true
                placeholderText: "Password"
                echoMode: TextInput.Password
                focus: true
                onAccepted: root.attemptLogin()
                transform: Translate { id: shakeOffset }

                SequentialAnimation {
                    id: shake
                    NumberAnimation { target: shakeOffset; property: "x"; to: 14; duration: 50 }
                    NumberAnimation { target: shakeOffset; property: "x"; to: -14; duration: 80 }
                    NumberAnimation { target: shakeOffset; property: "x"; to: 0; duration: 50 }
                }
            }

            Button {
                id: signIn
                Layout.fillWidth: true
                Layout.preferredHeight: 46 * root.unit
                text: "Sign in"
                enabled: password.text.length > 0
                onClicked: root.attemptLogin()
                contentItem: Text {
                    text: signIn.text
                    color: root.color
                    font.family: root.fontFamily
                    font.pixelSize: 16 * root.unit
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 10 * root.unit
                    // Fade the colors, not the item, so the disabled state stays a clean flat tint.
                    color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.35)
                    gradient: signIn.enabled ? enabledGradient : null
                    Gradient {
                        id: enabledGradient
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: root.accent }
                        GradientStop { position: 1.0; color: root.accent2 }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                Layout.minimumHeight: 20 * root.unit
                text: root.statusText
                color: root.statusText.indexOf("Wrong") === 0 ? root.errorColor : root.muted
                font.family: root.fontFamily
                font.pixelSize: 14 * root.unit
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // ---- Session and power, bottom right ------------------------------------------------
    RowLayout {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 48 * root.unit
        spacing: 10 * root.unit

        ComboBox {
            id: session
            model: sessionModel
            textRole: "name"
            // SDDM remembers the last session; offer IRAM OS when there is no history.
            objectName: "sessionBox"
            // SDDM remembers the last session. With no history, offer IRAM OS. This runs
            // after the model is populated: find() would see no entries in a binding.
            Component.onCompleted: {
                var iram = find("IRAM OS")
                currentIndex = sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : Math.max(0, iram)
            }
            Layout.preferredWidth: 220 * root.unit
            Layout.preferredHeight: 40 * root.unit
            font.family: root.fontFamily
            font.pixelSize: 14 * root.unit
            contentItem: Text {
                leftPadding: 14 * root.unit
                text: session.displayText
                color: root.fg
                font: session.font
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: 10 * root.unit
                color: Qt.rgba(root.color.r, root.color.g, root.color.b, 0.7)
                border.width: 1
                border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.4)
            }
        }

        Repeater {
            model: [
                { glyph: "\u{f04b2}", label: "Suspend", action: "suspend", capability: "canSuspend" },
                { glyph: "\u{f0709}", label: "Restart", action: "reboot", capability: "canReboot" },
                { glyph: "\u{f0425}", label: "Shut down", action: "powerOff", capability: "canPowerOff" }
            ]
            delegate: Button {
                required property var modelData
                visible: root[modelData.capability] === true
                Layout.preferredWidth: 40 * root.unit
                Layout.preferredHeight: 40 * root.unit
                ToolTip.visible: hovered
                ToolTip.text: modelData.label
                Accessible.name: modelData.label
                onClicked: root.power(modelData.action)
                contentItem: Text {
                    text: modelData.glyph
                    color: parent.hovered ? root.accent : root.fg
                    font.family: root.fontFamily
                    font.pixelSize: 18 * root.unit
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 10 * root.unit
                    color: Qt.rgba(root.color.r, root.color.g, root.color.b, 0.7)
                    border.width: 1
                    border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.4)
                }
            }
        }
    }

    Component.onCompleted: password.forceActiveFocus()
}
