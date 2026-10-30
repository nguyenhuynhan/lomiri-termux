# Khôi phục System Settings gốc — 30/10/2026

Settings tự viết được giữ ở commit `69bb7ce` (`feat: add private Lomiri session
settings`). Trong phiên hiện tại, app đó mang tên **Session Settings**;
**System Settings** là app Lomiri gốc. Cả hai được giữ trên branch
`codex/native-system-settings`.

## Nguyên nhân và cách khôi phục

Debian đã cài `lomiri-system-settings 1.3.1-6`, nhưng overlay shell của project
tạo desktop entry `Hidden=true`. Adapter PRoot cũng chưa cho phép app này.
Đã bỏ shadow, chép desktop entry nguyên bản vào XDG data riêng, cho phép đúng
binary trong adapter và thêm icon native vào dock một lần, giữ các mục đã ghim.

PluginManager native quét GenericDataLocation và giữ manifest cuối cùng có cùng
tên. Riêng app native dùng `/usr/local/share:/usr/share:<runtime>/native-data`.
Manifest Background/Sound trong thư mục cuối trỏ tới bản sao plugin gốc có vá;
không sửa plugin package để áp dụng các bản vá này.

- Background dùng `com.lomiri.Shell background-picture-uri` trong profile riêng,
  thay đường ghi AccountsService chưa có trong PRoot. Giữ backend gốc cho danh
  sách ảnh và chuẩn bị file. Thêm null guards cho delegates/preview header và
  tính chiều cao grid tường minh để tránh binding loop.
- Dock và Session Settings dùng chung `com.lomiri.Shell launcher-width` với
  slider native. Giá trị dock-height cũ được chuyển một lần, không reset profile.
- Khởi chạy Ayatana sound service thật trong group của phiên. Sound plugin xử lý
  tên âm thanh trống và trạng thái D-Bus chưa có. Không mô phỏng dịch vụ phần cứng.
- Frontend 1.3.1 được build riêng từ source archive Debian, với ba null guards
  ở anchors của searchField giống bản upstream. Đây là nguồn app gốc, không viết
  lại màn hình. Các native libraries/plugins đã cài tiếp tục được dùng.

Archive SHA256: `cca7ea7bee4202b3ab6f29d601efadfdf40f2500165542a778c8e40ddfc461e5`,
đối chiếu `lomiri-system-settings_1.3.1-6.dsc`. Build record chứa cả hash binary
package và frontend. Adapter kiểm tra chúng trước khi chạy bản build riêng.

## Kiểm chứng trên OnePlus 13

- System Settings gốc hiện trong menu cùng Session Settings, có icon riêng ở dock.
- Mở Background & Appearance, xem System art, mở Preview và bấm Set: ghi được
  `Bridge_by_Sander_Klootwijk.jpg`; đọc lại từ process khác và sau cold restart.
  Đã trả hình nền về `lomiri-default-background.png` sau phép thử.
- Công tắc environment theme và blur ghi được cấu hình thật. Để lại dark
  environment (`light-mode=false`) và blur bật.
- Native app theme đổi Ambiance -> SuruDark -> Ambiance trong `theme.ini` riêng.
  Sau dùng frontend mới, hai lần đổi cuối không còn ba TypeError searchField.
- Slider Desktop & Launcher đổi launcher-width 7 -> 10 -> 7; dock và app icons
  đổi cỡ ngay. Giá trị giữ qua restart.
- Trang Sound mở với dịch vụ Ayatana có real D-Bus actions. Không xác nhận
  âm lượng nghe thực, ringtone, rung, SIM hay điều khiển Android.
- `tests/native-settings-services.py` qua: desktop package nguyên bản, native
  frontend có trong memory maps (PRoot /proc/exe trỏ loader), PID/group/profile
  đúng, duplicate không đổi PID, stop chỉ đóng native và giữ PID Calculator,
  mở lại sau stop được.
- `tests/settings-shell.py` qua trên Xvfb riêng; Bash syntax, Python parse và
  `git diff --check` qua. Không coi Xvfb là bằng chứng input/rotation trên máy.
- App đổi bố trí khi xoay ngang/dọc. Có một vòng renderer giữ vùng vẽ cũ sau
  resize; cold restart ở portrait khôi phục đầy đủ. Chưa coi rotation/redraw
  lâu dài là ổn định. Chính sách Android được trả về tự xoay sau kiểm tra.

## Giới hạn và lỗi giữ lại

Thử gọi thẳng binary trước khi restore metadata/adapter làm shell SIGSEGV ở
SessionAuthorizer. Khởi chạy qua UAL sau đó không tái hiện trong các lần thử;
chưa xác định đầy đủ nguyên nhân của đường gọi thẳng. Dùng menu/dock của phiên.
Một lần Not connected khác không có crash; shell/app vẫn chạy.

System bus, AccountsService, logind và các dịch vụ hardware Android chưa được
kết nối đủ. Wi-Fi/Bluetooth/Hotspot/SIM, timezone hệ thống, bảo mật và reset
thiết bị chưa được xác nhận hoạt động. Hotspot setup có thể báo thiếu module
Cellular; About/entry components còn cảnh báo anchors, cùng cảnh báo QML
deprecated và llvmpipe performance. Không ghi nhận các mục này là đã sửa hết.

Log/ảnh nằm trong runtime và artifacts ngoài Git. Backup trước restore:
`runtime/backup-native-settings-20261030/`.

## Dựng lại và quay về binary package

Trong Termux của project:

```bash
bash scripts/install-core-apps.sh
bash scripts/build-native-settings.sh
lomiri-stop
lomiri-start
```

Build script chỉ cài công cụ build trong Debian và xuất frontend vào runtime;
không ghi đè `/usr/bin/lomiri-system-settings`. Nếu muốn dùng lại binary package,
dừng phiên và đổi tên `runtime/native-build/build.json` trước khi mở lại.
Các bản vá plugin vẫn nằm trong runtime/native-data; source package được giữ.
