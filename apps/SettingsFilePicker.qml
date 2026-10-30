import QtQuick 2.15
import Qt.labs.folderlistmodel 2.12
import Lomiri.Components 1.3

Rectangle {
    id: picker
    property bool light: false
    function gu(value) { return units.gu(value) + units.gridUnit * 0; }
    signal selected(string uri)
    signal cancelled()
    color: light ? "#f4f4f8" : "#181922"
    MouseArea { anchors.fill: parent }
    FolderListModel {
        id: files
        folder: "file:///usr/share/backgrounds"
        nameFilters: ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.svg", "*.PNG", "*.JPG", "*.JPEG"]
        showDirs: true
        showDotAndDotDot: false
        showHidden: false
        sortField: FolderListModel.Name
    }
    Column {
        id: top
        x: picker.gu(2); y: picker.gu(2); width: parent.width - picker.gu(4); spacing: picker.gu(1)
        Text { text: "Chọn hình nền"; color: picker.light ? "#242532" : "white"; font.pixelSize: picker.gu(2.8); font.bold: true }
        Text { width: parent.width; text: decodeURIComponent(files.folder.toString().replace("file://", "")); color: picker.light ? "#626375" : "#b6b7c7"; wrapMode: Text.WrapAnywhere; font.pixelSize: picker.gu(1.6) }
        Rectangle {
            width: parent.width
            height: picker.gu(6)
            radius: picker.gu(1)
            color: picker.light ? "white" : "#30313d"
            border.color: location.activeFocus ? "#ff9955" : "#626375"
            TextInput {
                id: location
                anchors.fill: parent; anchors.margins: picker.gu(1.2)
                color: picker.light ? "#242532" : "white"
                font.pixelSize: picker.gu(1.8)
                verticalAlignment: TextInput.AlignVCenter
                clip: true; selectByMouse: true
                inputMethodHints: Qt.ImhUrlCharactersOnly | Qt.ImhNoPredictiveText
            }
            Text {
                anchors.fill: parent; anchors.margins: picker.gu(1.2)
                text: "Đường dẫn thư mục hoặc ảnh trên máy"
                visible: location.text.length === 0 && !location.activeFocus
                verticalAlignment: Text.AlignVCenter
                color: picker.light ? "#626375" : "#b6b7c7"
                font.pixelSize: picker.gu(1.6)
            }
        }
        Row {
            width: parent.width; spacing: picker.gu(1)
            SettingsChoice { width: (parent.width - 2 * parent.spacing) / 3; text: "Lên"; light: picker.light; onClicked: files.folder = files.parentFolder }
            SettingsChoice {
                width: (parent.width - 2 * parent.spacing) / 3; text: "Đi tới"; light: picker.light
                onClicked: {
                    var path = location.text.trim();
                    if (path.charAt(0) === "/") path = "file://" + path;
                    if (path.indexOf("file:///") !== 0) { location.text = ""; location.forceActiveFocus(); return; }
                    if (/\.(png|jpe?g|webp|svg)$/i.test(path)) picker.selected(path); else files.folder = path;
                }
            }
            SettingsChoice { width: (parent.width - 2 * parent.spacing) / 3; text: "Hủy"; light: picker.light; onClicked: picker.cancelled() }
        }
    }
    ListView {
        anchors.top: top.bottom; anchors.topMargin: picker.gu(2)
        anchors.bottom: parent.bottom; width: parent.width; clip: true
        model: files
        delegate: Rectangle {
            width: ListView.view.width; height: picker.gu(8)
            color: touch.pressed ? "#c94e24" : "transparent"
            Image { x: picker.gu(2); anchors.verticalCenter: parent.verticalCenter; width: picker.gu(6); height: width; source: fileIsDir ? "" : fileUrl; fillMode: Image.PreserveAspectCrop; asynchronous: true }
            Text {
                x: picker.gu(10); anchors.verticalCenter: parent.verticalCenter; width: parent.width - picker.gu(12)
                text: (fileIsDir ? "▸ " : "") + fileName; elide: Text.ElideMiddle
                color: picker.light ? "#242532" : "white"; font.pixelSize: picker.gu(1.9)
            }
            MouseArea { id: touch; anchors.fill: parent; onClicked: { if (fileIsDir) files.folder = fileUrl; else picker.selected(fileUrl.toString()); } }
        }
    }
}
