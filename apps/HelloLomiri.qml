import QtQuick 2.12
import QtQuick.Window 2.12

Window {
    id: app
    width: 400
    height: 640
    visible: true
    visibility: Window.Maximized
    title: "Lomiri client probe"
    color: "#15202b"
    property int taps: 0
    onTapsChanged: console.log('POC_INPUT taps=' + taps)

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24
        Text {
            text: "Hello Lomiri"
            color: "#f6f5f4"
            font.pixelSize: 30
        }
        Text {
            width: parent.width
            text: "Ứng dụng Qt thật để kiểm tra mở cửa sổ, cảm ứng và bàn phím."
            wrapMode: Text.WordWrap
            color: "#c9d5df"
            font.pixelSize: 18
        }
        Rectangle {
            width: parent.width
            height: 64
            radius: 12
            color: touch.pressed ? "#d25c37" : "#e8794f"
            Text {
                anchors.centerIn: parent
                text: "Chạm thử: " + app.taps
                color: "white"
                font.pixelSize: 21
            }
            MouseArea {
                id: touch
                anchors.fill: parent
                onClicked: app.taps++
            }
        }
        Rectangle {
            width: parent.width
            height: 64
            radius: 10
            color: "#253746"
            border.color: field.activeFocus ? "#e8794f" : "#576979"
            TextInput {
                id: field
                anchors.fill: parent
                anchors.margins: 16
                color: "white"
                font.pixelSize: 20
                verticalAlignment: TextInput.AlignVCenter
                clip: true
                selectByMouse: true
                onActiveFocusChanged: console.log('POC_INPUT field-focus=' + activeFocus)
                onTextChanged: console.log('POC_INPUT text-length=' + text.length)
            }
        }
        Text {
            width: parent.width
            text: "Chạm ô phía trên rồi mở bàn phím Android để nhập chữ."
            color: "#a7bbc9"
            wrapMode: Text.WordWrap
            font.pixelSize: 16
        }
        Text {
            text: "Cửa sổ: " + app.width + " × " + app.height
            color: "#a7bbc9"
            font.pixelSize: 16
        }
    }
}
