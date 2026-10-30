import QtQuick 2.15
import Lomiri.Components 1.3

Rectangle {
    id: choice
    property string text
    property bool selected: false
    property bool light: false
    function gu(value) { return units.gu(value) + units.gridUnit * 0; }
    signal clicked()
    height: choice.gu(6)
    radius: choice.gu(1)
    color: touch.pressed ? "#e57b4d" : selected ? "#c94e24" : light ? "#e8e8ef" : "#30313d"
    border.color: selected ? "#ff9955" : light ? "#d0d0da" : "#50515e"
    Text {
        anchors.centerIn: parent
        text: choice.text
        color: choice.selected ? "white" : choice.light ? "#242532" : "#f5f5fa"
        font.pixelSize: choice.gu(1.9)
    }
    MouseArea {
        id: touch
        anchors.fill: parent
        onClicked: choice.clicked()
    }
}
