# Kiểm tra ngày 30/10/2026

Thiết bị: OnePlus 13 (PJZ110), Android 17, Termux 0.118.3, Termux:X11 1.03.01-8ebcf1e-21.10.26. Lomiri chạy trong container Debian trixie riêng; Ubuntu 24.04 và desktop XFCE hiện có được giữ nguyên.

## Đã sửa và kiểm tra

| Phần | Kết quả và bằng chứng |
| --- | --- |
| Mở app từ menu | Adapter trên session bus riêng xử lý phần giao thức UAL cần dùng. Chỉ cho phép app/executable đã định nghĩa, kiểm tra danh tính phiên và PGID. Người dùng xác nhận mở app được. |
| Nhận diện tiến trình | Registry `runtime/app-pids` dùng biến UAL có sẵn `LOMIRI_APP_LAUNCH_SYSTEMD_CGROUP_ROOT`, bao gồm descendants trong PGID đã kiểm tra. Đây là metadata, không phải kernel cgroups hay cách ly tài nguyên. |
| Shortcut VSCode | Dùng cùng UAL với menu, desktop entry single-instance. Gọi hai lần giữ một tiến trình; lần hai trả lời ngay. Chọn icon ứng dụng để đưa cửa sổ đang chạy lên trước. |
| Mở ngay sau cold start | Tái hiện tiến trình chạy nhưng kẹt logo vì gọi app trước khi QML/application manager sẵn sàng. Startup và shortcut chờ marker `LOMIRI_SHELL_READY` sau khi shell tạo xong; cold start mở lại VSCode đã hiện editor, không còn log `Gave up waiting for signal listeners` trong lần thử cuối. |
| Xoay màn hình | Tái hiện xoay kép Android/Lomiri và cửa sổ giữ kích thước cũ. Overlay riêng bỏ lần xoay thừa, bind kích thước QScreen, chọn phone/tablet theo viewport. Người dùng xác nhận dùng được, tạm chấp nhận. |
| Focus shell | Bổ sung hàm `notifyAppFocusRequested` thiếu trong ShimGreeter của chế độ shell. Log phiên cuối không còn TypeError này. Không thay khóa máy Android. |
| VSCode Save As | Hộp thoại GTK không lưu được trong lần thử. Chuyển sang `files.simpleDialog.enable=true`; tạo, nhập và lưu cùng nội dung thành công, đọc lại file trên đĩa. |
| Python VSCode | Extension từng chọn Python 3.14.8 của Termux trong khi terminal dùng Debian. Chọn lại `/usr/bin/python3` (3.13.5), đặt default interpreter và launch config cho workspace thử. Sau restart log extension vẫn chọn `/usr/bin/python3`. |
| Chạy Python | GUI tạo/lưu `runtime/code-workspace/smoke-20261030.py`; terminal và lệnh Run Python cho output `LOMIRI_SMOKE_20261030`. Log debugpy xác nhận DAP adapter khởi động bằng `/usr/bin/python3`; chưa kiểm tra breakpoint/step đầy đủ. |
| Bộ app cơ bản | Đã cài và khởi động qua UAL: Terminal, File Manager, Calculator, Clock, Calendar, Gallery, Media Player. Có script `scripts/install-core-apps.sh` để tái lập. |
| Chọn media | Cài content-hub và multimedia plugins; picker Media Player đã thấy File Manager, thay cho thông báo không có provider. Chưa kiểm chứng phát video đầy đủ. |
| Audio | Unix socket lỗi protocol do UID mô phỏng PRoot. Endpoint TCP chỉ listen 127.0.0.1, cổng riêng và cookie của Termux đã cho guest kết nối tới `OpenSL_ES_sink`. Stop phiên đã gỡ đúng module riêng, giữ daemon audio chung. Chưa xác nhận nghe từ loa. |

## Kiểm tra tự động

- 3 tests ownership/lifecycle đều qua.
- Live probe UAL: khởi động Calculator, kiểm tra PID registry/PGID, từ chối unit lạ, dừng app và nhận exit đều qua.
- Test viewport Xvfb qua sau khi cài dependency Xvfb còn thiếu ở lần đầu.
- Bash syntax và Python parse đều qua.
- Stop/start phiên thật, audio module cleanup và gọi VSCode hai lần đã kiểm tra.

## Còn giới hạn

- Laban Key: ASCII `abc`, `hello` vào editor/terminal được. Chuỗi xử lý dấu Telex có ký tự lặp/mất; chưa sửa tiếng Việt có dấu. Đã trả `enforceCharBasedInput=false` như ban đầu, không đổi bàn phím mặc định.
- Chưa kiểm chứng đầy đủ breakpoint/step, extension đăng nhập, phát video, báo thức khi Android ngủ, đồng bộ lịch/tài khoản, GPU/pin và độ ổn định dài hạn.
- Đây là Lomiri trong Android, chưa phải Ubuntu Touch native. SIM, camera, Bluetooth và quản lý phần cứng vẫn cần Android; không unlock bootloader hay đổi SELinux.

Scripts/log ban đầu và settings VSCode đã sao lưu trên điện thoại tại `~/projects/lomiri-termux/runtime/backup-20261030/`. Mã và profile chỉ được sửa trong project riêng; không commit/push. Ảnh/log thô ở `runtime/` trên điện thoại và `artifacts/` tại workspace, không đưa vào Git.
