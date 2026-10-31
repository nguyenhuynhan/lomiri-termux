import QtQuick 2.15
import QtQuick.Window 2.12
import Lomiri.Components 1.3
import GSettings 1.0

Window {
    id: app
    width: 480
    height: 760
    visible: true
    title: "Session Settings"
    color: light ? "#f4f4f8" : "#181922"
    property bool light: shellSettings.lightMode
    property color ink: light ? "#242532" : "#f5f5fa"
    property color muted: light ? "#626375" : "#b6b7c7"
    property string notice: "Thay đổi được lưu tự động."
    property string candidateWallpaper: ""
    property bool schemasReady: shellSettings.schema.isValid && hostSettings.schema.isValid && launcherSettings.schema.isValid
    function gu(value) { return units.gu(value) + units.gridUnit * 0; }

    GSettings { id: shellSettings; schema.id: "com.lomiri.Shell" }
    GSettings { id: hostSettings; schema.id: "com.lomiri.Termux" }
    GSettings { id: launcherSettings; schema.id: "com.lomiri.Shell.Launcher" }
    Component.onCompleted: units.gridUnit = 8 * hostSettings.uiScale
    Connections {
        target: shellSettings
        function onChanged(key, value) { app.notice = "Đã lưu thay đổi."; }
    }
    Connections {
        target: hostSettings
        function onChanged(key, value) {
            units.gridUnit = 8 * hostSettings.uiScale;
            app.notice = "Đã lưu thay đổi.";
        }
    }
    Connections {
        target: launcherSettings
        function onChanged(key, value) { app.notice = "Đã lưu danh sách ghim."; }
    }

    function pinned(id) { return launcherSettings.items.indexOf("application:///" + id + ".desktop") >= 0; }
    function togglePin(id) {
        var uri = "application:///" + id + ".desktop";
        var items = launcherSettings.items.slice();
        var index = items.indexOf(uri);
        if (index >= 0) items.splice(index, 1); else items.push(uri);
        launcherSettings.items = items;
    }
    function previewWallpaper(path) {
        var uri = path.trim();
        if (uri.charAt(0) === "/") uri = "file://" + uri;
        if (uri.indexOf("file:///") !== 0) {
            app.notice = "Chọn ảnh trên máy, với đường dẫn bắt đầu bằng / hoặc file:/// .";
            return;
        }
        candidateWallpaper = "";
        candidateWallpaper = uri;
    }
    function restoreAppearance() {
        shellSettings.schema.reset("light-mode");
        shellSettings.schema.reset("enable-blur");
        shellSettings.schema.reset("background-picture-uri");
        hostSettings.schema.reset("ui-scale");
        hostSettings.schema.reset("dock-height");
        shellSettings.schema.reset("launcher-width");
        hostSettings.schema.reset("drawer-shortcut");
        hostSettings.schema.reset("mode-shortcut");
        candidateWallpaper = "";
        app.notice = "Đã khôi phục giao diện và phím tắt mặc định.";
        confirmReset.visible = false;
    }

    Rectangle {
        id: header
        width: parent.width
        height: app.gu(11)
        color: app.light ? "white" : "#22232f"
        Column {
            anchors.left: parent.left; anchors.leftMargin: app.gu(2.5)
            anchors.verticalCenter: parent.verticalCenter
            spacing: app.gu(.5)
            Text { text: "Cài đặt"; color: app.ink; font.pixelSize: app.gu(3.4); font.bold: true }
            Text { text: "Phiên Lomiri"; color: app.muted; font.pixelSize: app.gu(1.8) }
        }
        SettingsChoice {
            anchors.right: parent.right; anchors.rightMargin: app.gu(2)
            anchors.verticalCenter: parent.verticalCenter
            width: app.gu(7); text: "Đóng"; light: app.light
            onClicked: app.close()
        }
    }

    Flickable {
        id: scroll
        anchors.top: header.bottom; anchors.bottom: footer.top
        width: parent.width
        contentHeight: content.height + app.gu(5)
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        enabled: app.schemasReady
        Column {
            id: content
            x: app.gu(2.5); y: app.gu(2.5)
            width: parent.width - app.gu(5)
            spacing: app.gu(2)

            Text { text: "Chế độ làm việc"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            Row {
                width: parent.width; spacing: app.gu(1)
                SettingsChoice { objectName: "mobileChoice"; width: (parent.width - parent.spacing) / 2; text: "Mobile"; light: app.light; selected: shellSettings.usageMode === "Staged"; onClicked: shellSettings.usageMode = "Staged" }
                SettingsChoice { objectName: "pcChoice"; width: (parent.width - parent.spacing) / 2; text: "PC"; light: app.light; selected: shellSettings.usageMode === "Windowed"; onClicked: shellSettings.usageMode = "Windowed" }
            }
            Text { width: parent.width; text: "Mobile mở app phủ vùng làm việc. PC có cửa sổ có thể di chuyển và thay đổi kích thước."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }

            Text { text: "Giao diện"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            Row {
                width: parent.width; spacing: app.gu(1)
                SettingsChoice { objectName: "darkChoice"; width: (parent.width - parent.spacing) / 2; text: "Tối"; light: app.light; selected: !app.light; onClicked: shellSettings.lightMode = false }
                SettingsChoice { objectName: "lightChoice"; width: (parent.width - parent.spacing) / 2; text: "Sáng"; light: app.light; selected: app.light; onClicked: shellSettings.lightMode = true }
            }
            Text { text: "Cỡ giao diện Lomiri · " + Math.round(hostSettings.uiScale * 100) + "%"; color: app.ink; font.pixelSize: app.gu(2) }
            Row {
                width: parent.width; spacing: app.gu(1)
                Repeater {
                    model: [0.85, 1.0, 1.15, 1.25]
                    SettingsChoice {
                        width: (content.width - app.gu(3)) / 4
                        text: Math.round(modelData * 100) + "%"; light: app.light
                        selected: Math.abs(hostSettings.uiScale - modelData) < .01
                        onClicked: hostSettings.uiScale = modelData
                    }
                }
            }
            Text { width: parent.width; text: "Đổi cỡ shell và Cài đặt ngay. VSCode và Firefox có tùy chọn cỡ chữ riêng."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }
            SettingsChoice {
                objectName: "blurChoice"; width: parent.width; light: app.light
                text: "Làm mờ nền menu: " + (shellSettings.enableBlur ? "Bật" : "Tắt")
                selected: shellSettings.enableBlur
                onClicked: shellSettings.enableBlur = !shellSettings.enableBlur
            }
            Text { width: parent.width; text: "Tắt làm mờ có thể giúp giao diện nhẹ hơn khi dựng hình bằng CPU."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }

            Text { text: "Dock"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            Row {
                width: parent.width; spacing: app.gu(1)
                Repeater {
                    model: [{label: "Gọn", value: 6}, {label: "Vừa", value: 7}, {label: "Lớn", value: 9}]
                    SettingsChoice {
                        width: (content.width - app.gu(2)) / 3
                        text: modelData.label; light: app.light; selected: shellSettings.launcherWidth === modelData.value
                        onClicked: shellSettings.launcherWidth = modelData.value
                    }
                }
            }
            Text { text: "Ứng dụng ghim"; color: app.ink; font.pixelSize: app.gu(2) }
            Flow {
                width: parent.width; spacing: app.gu(1)
                Repeater {
                    model: [
                        {name: "Cài đặt", id: "lomiri-session-settings"}, {name: "Terminal", id: "lomiri-terminal-app"},
                        {name: "Tệp", id: "lomiri-filemanager-app"}, {name: "VSCode", id: "lomiri-code"},
                        {name: "ChatGPT", id: "lomiri-chatgpt"}, {name: "Máy tính", id: "lomiri-calculator-app"},
                        {name: "Đồng hồ", id: "lomiri-clock-app"}, {name: "Lịch", id: "lomiri-calendar-app"},
                        {name: "Ảnh", id: "lomiri-gallery-app"}, {name: "Media", id: "lomiri-mediaplayer-app"}
                    ]
                    SettingsChoice {
                        width: (content.width - app.gu(1)) / 2
                        text: (selected ? "✓ " : "+ ") + modelData.name; light: app.light
                        selected: app.pinned(modelData.id); onClicked: app.togglePin(modelData.id)
                    }
                }
            }

            Text { text: "Hình nền"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            Image {
                id: wallpaperPreview
                width: parent.width; height: app.gu(18)
                fillMode: Image.PreserveAspectCrop; clip: true; asynchronous: true
                source: app.candidateWallpaper || shellSettings.backgroundPictureUri
                onStatusChanged: {
                    if (app.candidateWallpaper && status === Image.Error) {
                        app.candidateWallpaper = "";
                        app.notice = "Không đọc được ảnh. Hình nền hiện tại vẫn được giữ.";
                    }
                }
            }
            Row {
                width: parent.width; spacing: app.gu(1)
                SettingsChoice { width: (parent.width - parent.spacing) / 2; text: "Mặc định"; light: app.light; onClicked: { shellSettings.schema.reset("background-picture-uri"); app.candidateWallpaper = ""; } }
                SettingsChoice { width: (parent.width - parent.spacing) / 2; text: "Chọn ảnh…"; light: app.light; onClicked: filePicker.visible = true }
            }
            SettingsChoice {
                width: parent.width; text: "Dùng ảnh này"; light: app.light
                visible: app.candidateWallpaper !== "" && wallpaperPreview.status === Image.Ready
                onClicked: { shellSettings.backgroundPictureUri = app.candidateWallpaper; app.candidateWallpaper = ""; }
            }

            Text { text: "Bàn phím"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            SettingsChoice {
                width: parent.width; light: app.light
                text: "Bộ gõ: " + (hostSettings.vietnameseInput ? "Tiếng Việt (Telex)" : "Tiếng Anh")
                onClicked: hostSettings.vietnameseInput = !hostSettings.vietnameseInput
            }
            SettingsChoice {
                width: parent.width; light: app.light
                text: "Tự hiện bàn phím: " + (hostSettings.autoKeyboard ? "Bật" : "Tắt")
                onClicked: hostSettings.autoKeyboard = !hostSettings.autoKeyboard
            }
            Text {
                width: parent.width
                text: "Chọn English trên bàn phím Android. Nút VN/EN trên dock đổi bộ gõ trong Lomiri."
                wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8)
            }

            Text { text: "Phím tắt"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            SettingsChoice {
                width: parent.width; light: app.light; text: "Danh sách app: " + hostSettings.drawerShortcut
                onClicked: hostSettings.drawerShortcut = hostSettings.drawerShortcut === "F8" ? "Ctrl+Alt+D" : "F8"
            }
            SettingsChoice {
                width: parent.width; light: app.light; text: "Mobile / PC: " + hostSettings.modeShortcut
                onClicked: hostSettings.modeShortcut = hostSettings.modeShortcut === "F9" ? "Ctrl+Alt+M" : "F9"
            }
            Text { width: parent.width; text: "Dùng bàn phím vật lý hoặc bàn phím có phím chức năng. Alt+Tab chuyển ứng dụng."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }

            Text { text: "Thiết bị & Android"; color: app.ink; font.bold: true; font.pixelSize: app.gu(2.4) }
            Text { width: parent.width; text: "Wi‑Fi, Bluetooth, độ sáng, âm lượng, bàn phím và quyền ứng dụng được chỉnh trong Cài đặt Android. Vuốt từ cạnh trên điện thoại để mở cài đặt nhanh."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }
            Text { width: parent.width; text: "Để giữ màn hình sáng: Preferences của Termux:X11 → Screen idle timeout → Never. Chọn System để dùng lại thời gian nghỉ của Android."; wrapMode: Text.WordWrap; color: app.muted; font.pixelSize: app.gu(1.8) }
            SettingsChoice { width: parent.width; text: "Khôi phục giao diện mặc định…"; light: app.light; onClicked: confirmReset.visible = true }
        }
    }
    Rectangle {
        id: footer
        anchors.bottom: parent.bottom; width: parent.width
        height: app.gu(6)
        color: app.light ? "white" : "#22232f"
        Text {
            anchors.fill: parent; anchors.margins: app.gu(1.2)
            text: app.schemasReady ? app.notice : "Thiếu cấu hình Cài đặt. Hãy khởi động lại phiên Lomiri."
            wrapMode: Text.WordWrap; verticalAlignment: Text.AlignVCenter
            color: app.schemasReady ? app.muted : "#ee8855"; font.pixelSize: app.gu(1.7)
        }
    }
    SettingsFilePicker {
        id: filePicker
        anchors.fill: parent; visible: false; light: app.light
        onSelected: { app.previewWallpaper(uri); visible = false; }
        onCancelled: visible = false
    }
    Rectangle {
        id: confirmReset
        anchors.fill: parent; visible: false; color: "#e6181922"
        MouseArea { anchors.fill: parent }
        Column {
            anchors.centerIn: parent; width: parent.width - app.gu(6); spacing: app.gu(2)
            Text { width: parent.width; text: "Khôi phục giao diện và phím tắt? Chế độ làm việc, ứng dụng đang mở và danh sách ghim được giữ."; color: "white"; wrapMode: Text.WordWrap; font.pixelSize: app.gu(2.2) }
            SettingsChoice { width: parent.width; text: "Khôi phục"; onClicked: app.restoreAppearance() }
            SettingsChoice { width: parent.width; text: "Hủy"; onClicked: confirmReset.visible = false }
        }
    }
}
