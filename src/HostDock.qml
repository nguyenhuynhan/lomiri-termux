import QtQuick 2.15
import Lomiri.Components 1.3
import Lomiri.Launcher 0.1

Rectangle {
    id: dock
    objectName: "hostBottomDock"
    height: units.gu(7)
    color: "#202027"
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
            color: appTouch.pressed ? "#555560" : model.focused ? "#373743" : "transparent"
            Icon {
                anchors.centerIn: parent
                width: units.gu(4.5)
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
                color: model.focused ? "#ff9955" : "#dddddd"
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
        anchors.right: modeButton.left
        height: parent.height
        width: height
        Rectangle {
            width: units.gu(2.8); height: units.gu(2.5)
            x: units.gu(2); y: units.gu(1.6)
            color: "transparent"; border.color: "#aaaaaa"; border.width: 2; radius: 3
        }
        Rectangle {
            width: units.gu(2.8); height: units.gu(2.5)
            x: units.gu(1.3); y: units.gu(2.3)
            color: "#202027"; border.color: "white"; border.width: 2; radius: 3
        }
        MouseArea {
            anchors.fill: parent
            onClicked: dock.overviewRequested()
        }
    }

    Rectangle {
        id: modeButton
        anchors.right: parent.right
        height: parent.height
        width: units.gu(9)
        color: modeTouch.pressed ? "#555560" : "#30303a"
        Text {
            anchors.centerIn: parent
            text: dock.desktopMode ? "PC" : "Mobile"
            color: "white"
            font.pixelSize: units.gu(1.8)
        }
        MouseArea {
            id: modeTouch
            anchors.fill: parent
            onClicked: dock.modeToggleRequested()
        }
    }
}
