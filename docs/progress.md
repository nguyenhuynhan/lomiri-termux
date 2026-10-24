# Nhật ký kiểm chứng

## 2026-10-24

- Ghép nối và kết nối ADB với OnePlus 13 thành công.
- Kiến trúc: ARM64; Ubuntu hiện tại: 24.04.5 LTS; dung lượng còn trống khoảng 279 GB.
- Ubuntu universe có Lomiri 0.2.1-10build1, QtMir 0.8.0~git20240131.2f99df3-1build5, Mir 2.14.1.
- Termux:X11 chưa chạy tại thời điểm kiểm tra. Có socket cũ X1; phép thử cần kiểm tra kết nối thật, không chỉ kiểm tra file socket.
- Đã cài gói trong Ubuntu: Lomiri 0.2.1, QtMir 0.8.0~git20240131, Mir 2.14.1; thêm khoảng 1,1 GB.
- Mesa 25.2.8 llvmpipe: GLX/OpenGL 4.5, OpenGL ES 3.2, EGL X11 1.5 khởi tạo thành công. Đây là render CPU, chưa kiểm chứng GPU.
- `miral-shell` chạy lồng X11 với output 480x800, driver `mir:x11`, renderer `mir:egl-generic`; phiên thử tự kết thúc sau 12 giây.
- Lomiri tạo screen model, tải QML và chuẩn bị expose màn hình, sau đó SIGSEGV. Cả `--mode=full-shell`, `--mode=shell` và `QSG_RENDER_LOOP=basic` đều chưa giải quyết được.
- Trong lần thử Ubuntu chưa thấy launcher/panel Lomiri hoạt động ổn định. Lỗi này được vượt qua khi chuyển sang bộ Debian mới hơn bên dưới.
- Stack trace chẩn đoán: signal 11, địa chỉ null, `PlatformScreen::makeCurrent` → `MirOpenGLContext::makeCurrent` → QtQuick expose/render. Nhánh QtMir trước Mir 2.20 dùng render target kiểu cũ; khả năng không tương thích với backend X11/generic renderer hiện tại là giả thuyết đang kiểm chứng.
- Đã tạo container riêng `lomiri-debian` từ image chính thức `debian:trixie`. Không nâng cấp Ubuntu lên Debian hay trộn kho hai distro.
- Bộ Debian cài thành công: Lomiri 0.5.0-2; Mir 2.20.2-2; QtMir 0.8.0~git20250407.ea2f477-1+deb13u1; Mesa llvmpipe 25.0.7.
- Lomiri Debian đã tạo output surface hợp lệ và không còn crash null render target của bộ Ubuntu. Đã thấy shell, launcher/drawer và danh sách ứng dụng Mir Shell/System Settings trên màn hình thật.
- Đã mở `HelloLomiri.qml` bên trong shell bằng Wayland và `DESKTOP_FILE_HINT`, với qmlscene 5.15.15. Chỉnh GRID_UNIT_PX=8 và scale ứng dụng về 1 giải quyết clipping do scale kép trong lần thử đầu.
- Chạm và nhập liệu chưa được xác nhận: ADB tap/text và phép thử X11 click/type chưa làm nút tăng số hoặc hiện chữ. Android keyboard có thể hiện, nhưng focus/input routing của client vẫn cần kiểm tra. Đã hỏi người dùng thử thực tế.
- Đã quan sát Termux:X11 chuyển ngang/dọc trong phiên. Cửa sổ PoC vẫn cố định 480x800 và có thể tràn chiều cao khi ngang; chưa đánh giá resize/rotation hoàn chỉnh.
- Đã stop/start lại phiên Debian thật; desktop XFCE vẫn hoạt động và mở app thử lại thành công.
- Những dịch vụ dựa vào systemd user/system bus chưa hoạt động đầy đủ trong PRoot. Launcher hiển thị không chứng minh tất cả app có thể mở qua app-launch.
- Ba test quản lý phiên đã chạy trên Termux và qua: stop đúng phiên, bỏ qua PID/start-time cũ, bỏ qua command khác.

## Tiếp tục công việc

Log trên điện thoại ở `~/projects/lomiri-termux/runtime/`:

- `install.log`: gói Ubuntu.
- `mir-probe.log`: backend Mir X11 đã khởi động.
- `session-first-crash.log`, `session-basic-crash.log`, `session-shell-crash.log`: các lần mở shell.
- `session.log`: lần gần nhất; trace chẩn đoán có nhãn `LOMIRI_CRASH_TRACE`.
- `debian-supervisor.log`, `install-debian.log`: container/gói Debian mới.

Mã upstream đã đọc chỉ để đối chiếu; chưa sửa hay build lại upstream. Snapshot Lomiri: `80583f6c633426df26af5666d1bb340579818c42`. Binary thử Ubuntu là bản đóng gói cũ hơn snapshot.

## 2026-10-24 — mở trực tiếp và bản vá input

- Theo yêu cầu người dùng, chuyển mặc định sang X server riêng `:2 -tag lomiri-poc`; không cần chạy XFCE trước. `lomiri-start` và shortcut Android Lomiri gọi `start-direct.sh`.
- Hai Android tasks từng dùng URI trần và URI có scheme nhưng cùng tag đã làm nhầm cửa sổ kết nối. Launch script thống nhất `termux-x11-window://lomiri-poc`; không cần thay APK.
- Đối chiếu đúng QtMir source revision `ea2f477`: pointer dispatcher post QMouseEvent vào QtEventFeeder, còn shell QWindow không nhận sự kiện. Constructor shim trước đó không giải quyết được lỗi.
- Bridge riêng interpose Qt notifier cho đúng QtEventFeeder, route mouse press/release/move tới shell QWindow. Loại bỏ interposer không dùng; giữ nguyên library hệ thống.
- Build với g++/Qt5Gui trong Debian. Test Qt offscreen qua: press/release, fractional coordinates, button/modifier state và unrelated receiver passthrough. Không preload thì presses=0/releases=0, tái hiện đúng lỗi.
- Đã khởi động bản bình thường với INPUT_TRACE=0, không tải QML chẩn đoán, không dùng input-probe/crash-trace. Log app xác nhận taps tăng và text length từ 1 tới 11; screenshot hiện helloLomiri.
- Thử từ phía Android: ADB touchscreen giữ/kéo nhẹ làm nút phản hồi; input text hiện AndroidInput; chạm hai phím Gboard làm chữ w/v xuất hiện trong app. Đây là input do công cụ mô phỏng trên thiết bị; chưa thay thế xác nhận thao tác tay của người dùng. Chưa kiểm tra tiếng Việt có dấu.
- Một số tap ADB cực ngắn không phản hồi; đã có một lần màn hình đen khi keyboard làm X output đổi kích thước. Map/raise/resize lại cửa sổ Mir đã phục hồi mà không restart guest. Chưa xác định nguyên nhân hay khẳng định đã sửa triệt để; resize/rotation còn cần hoàn thiện.
- Guard startup ghi package versions/hash bridge, từ chối ABI cũ sau nâng cấp Qt/QtMir; build lại bằng scripts/build-input-compat.sh.
- Đăng ký dynamic shortcuts Lomiri và Stop Lomiri qua Termux:Widget; giữ Linux Desktop và Ubuntu Terminal. dumpsys shortcut xác nhận cả bốn.
- Test lifecycle thực tế: lomiri-stop đóng X2, X1 còn đáp ứng; gọi lomiri-start hai lần giữ cùng PID. Ba test ownership guards trên Termux vẫn qua.
- Chưa commit, push, publish; toàn bộ thay đổi là project và runtime riêng trên điện thoại/máy tính.

## 2026-10-24 — xác nhận thao tác trực tiếp

- Người dùng trả lời “Chạm và nhập đều được” sau khi thử nút Chạm thử và ô nhập trong Hello Lomiri trên OnePlus 13.
- Cập nhật trạng thái: input cơ bản đã được xác nhận bằng thao tác trực tiếp của người dùng, ngoài bằng chứng tự động trước đó.
- Xác nhận này chưa bao phủ tiếng Việt có dấu, gesture/scroll, resize/rotation, dùng lâu hoặc pin/GPU.

## 2026-10-24 — ứng dụng làm việc và repo cộng đồng

- Repo public nguyenhuynhan/lomiri-termux đã tạo và nhận mã nguồn, MIT license cho code gốc, hướng dẫn tiếng Anh/Vietnamese và CONTRIBUTING. Gitleaks không phát hiện secret; không đưa runtime/profile/screenshot thô lên Git.
- CI đầu trên x86 không interpose được Qt notifier nội bộ; chuyển sang ARM64 đúng target. CI ARM64 đã qua ownership tests, real Qt input test và test viewport với Xvfb (resize, cửa sổ khác, stale owner).
- Cài Microsoft VSCode ARM64 1.143.1-1792691836 từ vendor, đối chiếu SHA256 với API release chính thức. Cài Firefox ESR 153.5.1esr-1~deb13u1 từ Debian. Không nhập profile của workstation cũ.
- Broker Unix socket riêng chỉ khởi động code/chatgpt; process app thuộc PGID của phiên. Thử dừng đã xác nhận 37 process ghi nhận thoát, X1 còn đáp ứng. Đã khởi động lại app sau đó.
- Thêm bridge X11 theo sự kiện để đồng bộ cửa sổ host Mir với viewport. Chỉ thao tác trong phiên direct đã xác thực owner, không thay cửa sổ khi root có nhiều child.
- Đã đóng Android task cũ tạo bằng URI trần cùng tag. Cửa sổ canonical hiện hiển thị đúng trên điện thoại, không còn nền Settings lọt vào lần kiểm tra đó.
- VSCode khởi động cần --no-sandbox trong PRoot; Firefox chạy với cấu hình mặc định. Profile/HOME/cache app mới ở runtime riêng. Người dùng tự chấp nhận Workspace Trust cho thư mục hello.py thử.
- Phép thử GUI đã sửa/lưu hello.py thành print("Lomiri VSCode works"), rồi terminal tích hợp chạy python3 hello.py và hiện đúng output. Microsoft Python extension đã hiện được cài trong profile riêng.
- Một số phím/chạm tiêm quá nhanh bị mất; dùng nhịp chậm hơn hoàn tất thử nghiệm. Alt+Tab và nút maximize của Lomiri hoạt động cho các cửa sổ đã thử.
- ChatGPT web chạy trong Firefox Wayland, gửi 2+2 và nhận 2 + 2 = 4 khi chưa đăng nhập; không kiểm tra phiên tài khoản hay nhập tiếng Việt có dấu.
- Theo yêu cầu giữ phone không khóa khi đi lâu, đặt Screen idle timeout của Termux:X11 thành Never (keep screen on), đã đọc lại giá trị. Cần để X11 ở phía trước; vẫn khóa bằng nút nguồn được. Không đo pin/GPU.
