# Kiến trúc PoC

## Luồng mặc định

```text
Android
  └─ Termux:X11 :2, tag lomiri-poc (cửa sổ Android riêng)
       └─ Mir X11 backend trong Debian lomiri-debian
            └─ QtMir + Lomiri shell
                 └─ Qt/Wayland clients
```

`lomiri-start` chạy `start-direct.sh`; không khởi động XFCE. `session.sh` sở hữu cả X server và guest trong một nhóm tiến trình riêng. Stop kiểm tra PID, thời điểm khởi tạo, process group và đường dẫn command trước khi gửi SIGTERM. Script không cưỡng bức kill tiến trình lạ.

Luôn dùng URI `termux-x11-window://lomiri-poc` khi mở activity. Trộn URI này với URI trần `lomiri-poc` tạo hai Android document tasks cùng tag; task cũ có thể bị mất kết nối.

Chế độ phát triển nested dùng `scripts/start.sh` trên X display hiện có `:1`; bộ XFCE/Code hiện tại tiếp tục dùng riêng.

## Đồ họa và input

Bộ đã thử: Lomiri 0.5.0-2, Mir 2.20.2-2, QtMir 0.8.0~git20250407.ea2f477-1+deb13u1, Qt 5.15.15, Mesa llvmpipe 25.0.7. GRID_UNIT_PX=8, Qt client scale=1. Phiên direct lấy kích thước output lúc khởi động; cập nhật layout theo keyboard/orientation còn là giới hạn.

Bộ Ubuntu 24.04 cũ crash ở QtMir `PlatformScreen::makeCurrent` với null render target. Debian Mir/QtMir mới đã vượt qua lỗi dựng hình đó. Không trộn package hay repository giữa hai distro.

QtMir đăng mouse event tới plain QObject `QtEventFeeder`. Bridge local trong `src/qt-mouse-dispatch-compat.cpp` interpose `QCoreApplication::notifyInternal2` cho đúng RTTI class và đúng loại mouse event. Nó gọi mouse interface của Qt5 với QWindow shell, tọa độ global đổi sang local, timestamp/buttons/modifiers gốc. Sự kiện và receiver khác đi qua notifier gốc; Qt giữ quyền sở hữu posted event.

Bridge được build trong guest và chỉ preload vào Lomiri. Test offscreen Qt kiểm chứng sự kiện tới QWindow; baseline không preload tái hiện lỗi. `check-input-compat.py` đối chiếu package versions và hash thư viện trước khi chạy. Nâng Qt/QtMir phải build lại; đây là workaround, chưa phải patch upstream.

## Cách ly và giới hạn

- Chạy guest bằng user `dev`; PRoot không có quyền root thật hay systemd PID 1.
- DBus session riêng và XDG directories trong project runtime; không đọc cấu hình/tài khoản AI.
- Hello Lomiri chạy trực tiếp với desktop-file hint của QtMir. Launcher hiển thị chưa chứng minh systemd app-launch hoạt động.
- Mặc định không dùng QML copy, input probe hoặc crash handler. Chẩn đoán là tùy chọn.
- Android quản lý khóa màn hình và vòng đời app; không có Linux suspend/hibernate thực sự qua PRoot.
- Không lấy wake lock. CPU rendering, pin, gesture và adaptive layout chưa đạt mức desktop dùng hằng ngày.

## Broker và viewport hiện tại

Broker Python tạo socket riêng trong runtime, chỉ chấp nhận hai tên app code/chatgpt. Nó được supervisor khởi động trong cùng process group, kiểm tra PGID trước khi nhận yêu cầu và spawn Wayland clients trong group đó. DISPLAY và các preload/library path của host được bỏ khỏi môi trường client; HOME/profile được cách ly trong runtime. VSCode dùng opt-in no-sandbox cho PRoot, Firefox giữ cấu hình mặc định.

Native display-sync.py xác thực owner bằng session-state, dùng X11 Structure/Substructure notifications để theo dõi root và đồng bộ đúng một host window. Nó không polling và dừng khi ownership thay đổi. Test Xvfb kiểm chứng resize, không sửa nhiều cửa sổ và bỏ qua state cũ; test này không thay thế việc kiểm tra mọi kiểu xoay/IME trên điện thoại.

Các task Android trùng tag nhưng khác data URI có thể giữ activity cũ không còn hiển thị đúng. Dùng URI canonical từ đầu; lần thử trên máy đã đóng task trùng tạo trong quá trình chẩn đoán. Không tự xóa task Android theo ID cố định trong script phát hành.
