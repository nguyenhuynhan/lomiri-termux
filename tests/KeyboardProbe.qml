import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    id: app
    visible: true
    width: 400; height: 640
    visibility: Window.Maximized
    title: "Keyboard probe"
    color: "#15202b"
    Column {
        anchors.fill: parent; anchors.margins: 24; spacing: 20
        Text { text: "Thử bàn phím"; color: "white"; font.pixelSize: 26 }
        Text {
            width: parent.width; wrapMode: Text.WordWrap; color: "#c9d5df"; font.pixelSize: 18
            text: "Chạm ô nhập, gõ tieengs vieetj bằng bàn phím English. Nút Đọc mẫu ghi nội dung thử vào log riêng."
        }
        Rectangle {
            width: parent.width; height: 80; color: "#253746"; radius: 10
            border.color: sample.activeFocus ? "#e8794f" : "#576979"
            TextInput {
                id: sample
                objectName: "keyboardSample"
                anchors.fill: parent; anchors.margins: 12; color: "white"
                font.pixelSize: 22; verticalAlignment: TextInput.AlignVCenter
                selectByMouse: true; clip: true
                onActiveFocusChanged: console.log("KEYBOARD_FOCUS " + activeFocus)
                Keys.onPressed: console.log("KEYBOARD_KEY " + event.key)
                onTextChanged: console.log("KEYBOARD_LENGTH " + text.length)
            }
        }
        Rectangle {
            width: parent.width; height: 70; radius: 10; color: "#e8794f"
            Text { anchors.centerIn: parent; text: "Đọc mẫu"; color: "white"; font.pixelSize: 22 }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    console.log("KEYBOARD_SAMPLE " + JSON.stringify(sample.text))
                    sample.focus = false
                    app.contentItem.forceActiveFocus()
                }
            }
        }
        Rectangle {
            width: parent.width; height: 70; radius: 10; color: "#445566"
            Text { anchors.centerIn: parent; text: "Xóa mẫu"; color: "white"; font.pixelSize: 22 }
            MouseArea {
                anchors.fill: parent
                onClicked: { sample.focus = false; app.contentItem.forceActiveFocus(); sample.text = "" }
            }
        }
    }
}
