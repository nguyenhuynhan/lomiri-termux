import QtQuick 2.15
import Lomiri.Components 1.3
import Lomiri.Launcher 0.1
import GSettings 1.0

Rectangle {
    id: dock
    objectName: "hostBottomDock"
    height: units.gu(shellPreferences.launcherWidth)
    color: lightMode ? "#f7f7fb" : "#202027"
    property bool lightMode: shellPreferences.lightMode
    GSettings { id: preferences; schema.id: "com.lomiri.Termux" }
    GSettings { id: shellPreferences; schema.id: "com.lomiri.Shell" }
    property bool desktopMode: false
    signal applicationSelected(string appId)
    signal drawerRequested()
    signal modeToggleRequested()
    signal overviewRequested()

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: wheel.accepted = true
    }

    Rectangle {
        anchors.top: parent.top
        width: parent.width
        height: 1
        color: "#53535c"
    }

    Item {
        id: home
        width: dock.height
        height: dock.height
        anchors.left: parent.left
        Rectangle {
            anchors.centerIn: parent
            width: units.gu(5)
            height: width
            radius: units.gu(1)
            color: homeTouch.pressed ? "#f6814c" : "#c94e24"
            Grid {
                anchors.centerIn: parent
                columns: 3
                spacing: units.gu(.35)
                Repeater {
                    model: 9
                    Rectangle { width: units.gu(.55); height: width; radius: 1; color: "white" }
                }
            }
        }
        MouseArea {
            id: homeTouch
            anchors.fill: parent
            onClicked: dock.drawerRequested()
        }
    }

    ListView {
        id: apps
        objectName: "hostDockApps"
        anchors.left: home.right
        anchors.right: overview.left
        height: parent.height
        orientation: ListView.Horizontal
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        model: LauncherModel
        delegate: Rectangle {
            width: dock.height
            height: dock.height
            color: appTouch.pressed ? "#777780" : model.focused ? (dock.lightMode ? "#dedee8" : "#373743") : "transparent"
            Icon {
                anchors.centerIn: parent
                width: dock.height * .64
                height: width
                source: model.icon
            }
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: units.gu(.35)
                anchors.horizontalCenter: parent.horizontalCenter
                width: model.focused ? units.gu(2) : units.gu(.65)
                height: units.gu(.4)
                radius: height / 2
                visible: model.running
                color: model.focused ? "#ee7733" : dock.lightMode ? "#626275" : "#dddddd"
            }
            MouseArea {
                id: appTouch
                anchors.fill: parent
                onClicked: dock.applicationSelected(model.appId)
            }
        }
    }

    Item {
        id: overview
        anchors.right: inputButton.left
        height: parent.height
        width: height
        Rectangle {
            width: units.gu(2.8); height: units.gu(2.5)
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: units.gu(.4)
            anchors.verticalCenterOffset: -units.gu(.4)
            color: "transparent"; border.color: "#aaaaaa"; border.width: 2; radius: 3
        }
        Rectangle {
            width: units.gu(2.8); height: units.gu(2.5)
            anchors.centerIn: parent
            color: dock.color; border.color: dock.lightMode ? "#444455" : "white"; border.width: 2; radius: 3
        }
        MouseArea {
            anchors.fill: parent
            onClicked: dock.overviewRequested()
        }
    }

    Rectangle {
        id: inputButton
        objectName: "hostInputModeButton"
        anchors.right: modeButton.left
        width: units.gu(5.5)
        height: parent.height
        color: inputTouch.pressed ? "#777780" : dock.lightMode ? "#e5e5ed" : "#30303a"
        Text {
            anchors.centerIn: parent
            text: preferences.vietnameseInput ? "VN" : "EN"
            color: preferences.vietnameseInput ? "#ee7733" : dock.lightMode ? "#242532" : "white"
            font.pixelSize: units.gu(1.8)
        }
        MouseArea {
            id: inputTouch
            anchors.fill: parent
            onClicked: preferences.vietnameseInput = !preferences.vietnameseInput
        }
    }

    Rectangle {
        id: modeButton
        anchors.right: parent.right
        height: parent.height
        width: units.gu(9)
        color: modeTouch.pressed ? "#777780" : dock.lightMode ? "#e5e5ed" : "#30303a"
        Text {
            anchors.centerIn: parent
            text: dock.desktopMode ? "PC" : "Mobile"
            color: dock.lightMode ? "#242532" : "white"
            font.pixelSize: units.gu(1.8)
        }
        MouseArea {
            id: modeTouch
            anchors.fill: parent
            onClicked: dock.modeToggleRequested()
        }
    }
}
