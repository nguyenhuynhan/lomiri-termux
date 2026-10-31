# Nhật ký kiểm chứng

## GPU client và kết nối lại — 2026-10-31

- ADB tự kết nối lại sau khi tắt/bật Wi-Fi. Phiên chính đã dừng, PID state cũ
  không tồn tại; không tự khởi động lại phiên chính.
- Thu 43 file log cũ và 54 file sau thử client; checksum manifest khớp. Tính lại
  đủ 8 record timing từ log local cho kết quả trùng JSON trên phone.
- Rút ngắn đường socket thử từ 114 xuống 94 byte bằng bản sao `runtime/gpu-zink`;
  probe EGL chạy qua PRoot khác kết nối được. Lỗi eglInitialize trước đó có phần
  do harness, chưa đủ để quy cho driver. Cấu hình/đường phiên chính giữ nguyên.
- Zink client vẫn fallback llvmpipe; LIBGL_KOPPER_DRI2 không cải thiện. KGSL client
  trong shell Zink tạo EGL context Adreno và Calculator ghi renderer Adreno,
  nhưng Lomiri SIGSEGV khi hiện surface. Diagnostic preload xác nhận signal 11,
  địa chỉ null, backtrace chưa chỉ ra hàm. Chưa coi app GPU là hoạt động ổn định.
- Shell KGSL thiếu EGL_EXT_image_dma_buf_import_modifiers nên không bật dmabuf
  import; Calculator vẫn llvmpipe. Zink shell + client software hiển thị Calculator,
  nhập `1+2` và tiếp tục chạy đến khi chủ động dừng. Chưa kiểm chứng dài hạn.
- Thêm client-backend/trace-crash cho script thử; ba script qua kiểm tra cú pháp.
  Cleanup các lượt mới đã kiểm chứng; không còn process thử cũ/mới. Trả phone về
  Android Home. Chưa đổi mặc định, commit hoặc push. Chi tiết ở
  [kết quả GPU](gpu-results-20261031.md).

## Thử GPU — tổng hợp 2026-10-31

- Đã thử lần lượt VirGL, Freedreno/KGSL và Zink/Turnip trên display `:3`, tag
  riêng và bản sao project. Cả ba đã render shell Lomiri bằng Adreno 830.
- KGSL và Zink qua GLX/EGL với Accelerated: yes, GL 4.6/GLES 3.2. VirGL qua EGL
  và shell, nhưng GLX timeout 25 giây; ANGLE GL thêm EGL_BAD_ACCESS.
- Thu hai lượt menu benchmark với `QSG_RENDER_TIMING`, 672×1339: CPU median
  30–31 ms/p95 44–45 ms; KGSL 8–9/26–32 ms; Zink 3–4/16 ms. VirGL lượt đầu
  22/41 ms. Đây là thời gian Qt render loop, chưa phải FPS presentation.
- KGSL/threaded chạy được nhưng không cải thiện phép thử: median 14/p95 34 ms.
- Calculator vẫn dùng llvmpipe trong KGSL/Zink; EGL Wayland client thất bại.
  VSCode đã hiển thị trong Zink, chưa xác nhận renderer thực tế. Mir vẫn fallback
  software buffers. Chưa đổi backend mặc định hoặc kết luận pin/thermal.
- Cài thêm VirGL/ANGLE; Mesa 27.0.0-devel git-eb3e7fd4f0 dùng prefix riêng với
  artifact SHA256 đã pin, không thay thư viện hệ thống guest. Dọn process thử
  theo identity; sửa cleanup cho broker còn sót khi startup thất bại.
- Ngày 31/10 cần kết nối ADB lại trước khi đọc trạng thái và tiếp tục thử.
  Chi tiết ở [kết quả GPU](gpu-results-20261031.md).
- Kết nối lại: ADB 37.0.1 tìm được dịch vụ kết nối chính qua mDNS, nhưng TCP
  timeout 10060; ARP điện thoại Unreachable, ping báo Destination host unreachable.
  Chờ khôi phục đường LAN hoặc USB; chưa xác minh trạng thái phone hiện tại hay
  thu raw log về workspace. Ba script GPU qua kiểm tra cú pháp Python tại local.

## Nghiên cứu GPU/UI — 2026-10-30

- Kiểm tra trực tiếp qua ADB: SM8750, Adreno830v2, Android 17; Termux có quyền
  đọc/ghi node `/dev/kgsl-3d0`. GPU busy/frequency sysfs trả Permission denied;
  chưa đo utilization, pin hoặc frame time khi thao tác.
- Phiên Lomiri hiện tại và Settings dùng llvmpipe/basic; Code có `--disable-gpu`
  và child `--use-gl=disabled`, terminal GPU off. GLX/EGL X11 trên `:2` xác nhận
  llvmpipe LLVM 19.1.7, Mesa 25.0.7-2+deb13u1, Accelerated: no. Output hiện tại
  672×1339, mode khoảng 59.84 Hz. Năm script ép renderer đã đối chiếu SHA256 khớp
  giữa workspace và phone.
- Mir 2.20.2 chọn egl-generic, nhưng log báo thiếu
  `EGL_WL_bind_wayland_display` và fallback software buffers; dmabuf import được
  bật chưa chứng minh app dùng buffer GPU. Host Mesa 26.2.5 không thay Mesa guest.
- Probe libEGL/libGLESv2 Android trong process riêng tạo context/pbuffer rồi
  giải phóng: EGL 1.5 Android, Qualcomm Adreno (TM) 830, GLES 3.2 driver
  V@0800.80.1, build date 09/28/26. Chưa benchmark hoặc chạy Lomiri bằng GPU.
- Đã nghiên cứu VirGL/ANGLE qua driver Android, Freedreno KGSL container và
  Turnip/Zink A830; ghi lộ trình, nguồn và tiêu chí đo trong
  [báo cáo GPU](gpu-performance-research-20261030.md). Chưa cài package, sửa
  cấu hình phone, restart phiên, commit hoặc push.

## Native System Settings — 2026-10-30

- Giữ Settings tự viết ở commit `69bb7ce`; đổi tên trong phiên thành
  Session Settings. Phần khôi phục native ở branch `codex/native-system-settings`.
- Khôi phục desktop entry package `lomiri-system-settings 1.3.1-6`, whitelist
  adapter, icon menu/dock và plugin overlay riêng. Nối hình nền với private
  GSettings, dùng launcher-width cho dock; khởi chạy Ayatana sound service thật.
- Build frontend gốc 1.3.1 từ archive đã đối chiếu SHA256 với Debian dsc, áp dụng
  null guards searchField giống upstream; không ghi đè binary package. Kiểm tra
  memory maps xác nhận app dùng bản build riêng.
- Máy thật: Preview/Set hình nền, persistence restart, theme/blur, slider dock,
  app theme hai chiều; native launch/single-instance/owned stop/reopen đều qua.
  Xvfb shell probe và syntax checks qua. Menu hiện hai app riêng.
- Có lỗi redraw sau một vòng rotation; cold portrait restart khôi phục đầy đủ.
  Các dịch vụ Android/system bus và cảnh báo native chưa được coi là đã sửa hết.
  Xem [báo cáo native Settings](native-settings-20261030.md) cho phạm vi và recovery.

## Settings — 2026-10-30

- Thêm Settings riêng cho phiên PRoot, schema private, desktop entry và giới hạn
  executable/script trong app services. Bộ chọn hình nền không cần native dialog.
- Đã mở Qt/Wayland client trên OnePlus 13, thử mode, theme, cỡ giao diện, ghim app,
  hình nền và lưu phím tắt. Sửa Binding loop, icon field và cỡ chỉ lưu mà chưa relayout.
- Sau khi người dùng xác nhận lưu việc, đã restart, mở Settings từ menu/dock,
  kiểm tra cỡ dock/shell, phím tắt, ngang/dọc, ảnh lỗi và reset/cancel. Mở lại Code;
  probe Settings giữ unit Code, test ownership hiện có và Xvfb shell đều qua.
- Xvfb tìm thêm lỗi wizard thiếu module cập nhật và workspace item null lúc
  init; sửa trong overlay. CLI UAL gọi lại Settings có thể chờ resume handshake;
  menu/dock đã kiểm tra chuyển cửa sổ cùng PID. Không báo CLI resume là hoàn thiện.
  Chi tiết và giới hạn trong `docs/settings-20261030.md`.

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


## 2026-10-30 — menu ứng dụng, rotation và VSCode

Đã sửa và kiểm tra menu/shortcut, rotation kép, Save As, interpreter Python và kết nối audio trong phiên PRoot riêng. Xem [báo cáo kiểm chứng](verification-20261030.md) để biết bằng chứng, phạm vi test và các lỗi còn lại.

## 2026-10-30 — dock cố định ở cạnh dưới

- Theo yêu cầu, phiên direct dùng `src/HostDock.qml`: hàng icon ngang luôn hiện, nút chín chấm mở drawer có sẵn, dùng cùng LauncherModel và đường activateApplication của Lomiri. Dải launcher dọc và vùng kéo từ cạnh trái được tắt trong overlay riêng.
- Thu ngắn Stage và available desktop area một khoảng bằng chiều cao dock (7 grid units); app toàn màn hình vẫn nằm phía trên dock. Chiều rộng/vị trí dock bind theo viewport, không xoay dock độc lập.
- Máy thật vẫn dùng Lomiri 0.5.0-2, Android 17, Termux:X11 1.03.01-8ebcf1e-21.10.26 và software rendering. Đã chạm dock để mở VSCode, mở drawer, mở Calculator và chuyển về VSCode hiện có; không tạo tiến trình Code thứ hai.
- Ảnh màn hình xác nhận dock ở dưới trong cả bốn hướng Android (0/90/180/270 độ), bao gồm VSCode F11 toàn màn hình. Đã trả Android về tự xoay sau kiểm tra. Nội dung VSCode chưa lưu được khôi phục sau restart; có backup workspace/Backups trong runtime.
- Bash syntax, 3 lifecycle tests, Qt input bridge thực và viewport Xvfb test đều qua. Probe app-services từ chối chạy vì Calculator thử đang mở, đúng điều kiện bảo vệ của test; không tính lần này là probe app-services đã qua. Không thấy lỗi QML liên quan HostDock; cảnh báo WorkspaceSwitcher `width of null` có sẵn lúc khởi động vẫn còn.
- Chưa thử hàng icon tràn khi mở rất nhiều app hoặc bàn phím Android với dock. Log và ảnh kiểm tra giữ ngoài Git.

## 2026-10-30 — chọn Mobile/PC và đóng ứng dụng

- Thêm nút Mobile/PC và nút đa nhiệm (hai cửa sổ chồng nhau) vào bên phải dock. Mode dùng GSettings `com.lomiri.Shell usage-mode` trong XDG config riêng: Staged cho mobile, Windowed cho PC; không đổi desktop bên ngoài project. Chuyển trực tiếp qua cơ chế convergence của Lomiri, không restart app.
- Chặn tự chọn usage-mode theo chuột/kích thước trong overlay OrientedShell: đã tái hiện PC tự trở về Staged khi xoay vì PRoot không có pointer devices. Sau sửa, xoay ngang/dọc vẫn đọc lại Windowed và dock vẫn hiện PC.
- PC dùng decoration native, chiều cao 5.5 GU cho thao tác chạm. Các nút đóng/thu nhỏ/khôi phục trên panel không cần hover; cửa sổ F11 vẫn có dải điều khiển. Mobile giữ phone/tablet theo viewport và panel gọn 3 GU.
- Trên máy thật đã chạm nút PC/Mobile và đọc lại GSettings từ tiến trình khác; đã phóng to Calculator, thu nhỏ (app vẫn chạy), chọn dock để hiện lại, rồi đóng bằng nút X (ListUnits không còn Calculator). VSCode đang có nội dung chưa lưu vẫn được giữ qua đổi mode.
- Nút đa nhiệm gọi spread có sẵn. Trong Mobile đã mở Calculator, mở đa nhiệm và vuốt thẻ Calculator lên: số unit Calculator từ 1 về 0, log exit status 0; Code tiếp tục chạy. Không coi việc chỉ đổi focus là đóng app.
- Bash syntax, Python parse, 3 lifecycle tests, real Qt input bridge đều qua. Live app-services probe đã chạy lại thành công trong phiên kiểm tra này (launch/PID/ownership/stop). Ảnh kiểm tra PC F11 ngang có nút điều khiển và dock; phần nội dung vẫn còn khoảng nền phía dưới trong lần đó. Có một ảnh đa nhiệm ngay sau xoay/đổi mode bị redraw đen một phần; chưa coi render/transition dưới llvmpipe là hoàn thiện.
- Đã trả mode Staged/Mobile, tự xoay Android và focus VSCode cuối phiên.
- Kiểm tra tiếp xác nhận vùng đen phía dưới còn tồn tại sau đổi mode/xoay, không chỉ là ảnh chụp giữa transition. Bổ sung binding width/height tường minh cho OrientedShell trong ShellScreen (trước đó chỉ có implicitWidth/implicitHeight). Sau restart đã thử lại PC -> ngang -> dọc -> Mobile, rồi lặp lại với F11 và đa nhiệm: shell/dock phủ hết viewport, không còn vùng đen phía dưới trong các lần thử cuối. Giữ ghi nhận khoảng nền PC F11 ở trên là giới hạn riêng chưa tối ưu.
