# Lomiri trên Termux

[English guide](README.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

Lomiri thật đã chạy trực tiếp trên OnePlus 13 qua Termux:X11. **Không cần mở XFCE trước.** Dự án trên điện thoại: `~/projects/lomiri-termux`.

Phiên dùng Debian trixie ARM64 trong container riêng `lomiri-debian`: Lomiri 0.5.0, Mir 2.20.2, QtMir 0.8.0~git20250407. Android tiếp tục quản lý điện thoại; Ubuntu `mobile-ubuntu` và bộ công cụ code hiện có dùng riêng.

## Mở và dừng

Nhấn giữ biểu tượng **Termux:Widget**, chọn **Lomiri**. Có thể kéo shortcut này ra màn hình chính. Shortcut **Stop Lomiri** dừng riêng phiên thử. Hai shortcut đã được đăng ký trên điện thoại.

Hoặc mở Termux và chạy:

```bash
lomiri-start
```

Lệnh tạo X display riêng `:2`, mở đúng cửa sổ Android `lomiri-poc`, rồi chạy Lomiri. Gọi lại sẽ mở cửa sổ của phiên đang chạy. XFCE không tham gia vào phiên này. Cách mở qua XFCE trước đây chỉ là bước thử backend đồ họa.

Lưu việc trước khi dừng:

```bash
lomiri-stop
```

Lệnh kiểm tra danh tính PID rồi dừng nhóm tiến trình riêng của dự án, gồm X server `:2`. Desktop XFCE trên `:1` vẫn chạy nếu bạn đã mở nó trước đó. Nếu còn phiên XFCE cần kết thúc, dùng `desk-stop` riêng.

PoC không tự khởi động cùng điện thoại và không lấy wake lock. Khóa màn hình không phải hibernate Linux; Android có thể đóng tiến trình nền. Muốn giảm hoạt động nền sau khi dùng, lưu file rồi `lomiri-stop`. Chưa đo mức tiêu thụ pin.

## Thử chạm và bàn phím

Mở terminal thứ hai trong Termux:

```bash
cd ~/projects/lomiri-termux
bash scripts/demo-app.sh
```

Trong **Hello Lomiri**, chạm nút để tăng số; chạm ô nhập rồi dùng nút hình bàn phím ở thanh Termux:X11 để mở Gboard. App là Qt/Wayland client thật trong shell.

Bản vá input riêng cho dự án đã làm click và nhập chữ hoạt động trong các phép thử. Đã kiểm tra cả X11 click/type và thao tác qua Android, gồm phím trên Gboard. Ngày 24/10/2026, người dùng thử trực tiếp trên OnePlus 13 và xác nhận “Chạm và nhập đều được”. Một số lần chạm ADB cực ngắn không được ghi nhận; độ ổn định khi dùng lâu vẫn cần đánh giá.

## VSCode và ChatGPT

Đã chạy Microsoft VSCode ARM64 **1.143.1** và Firefox ESR **153.5.1** như Wayland client trong Lomiri. Phép thử đã sửa/lưu `hello.py` qua giao diện VSCode rồi chạy Python trong terminal tích hợp. ChatGPT web đã nhận `2+2` và trả lời `4` trong Firefox, chưa đăng nhập tài khoản.

Trên điện thoại đã cài xong, dùng:

```bash
lomiri-code
lomiri-chatgpt
```

Alt+Tab đổi cửa sổ; nút ô vuông trên thanh tiêu đề của Lomiri phóng to app. Shortcut Android có tên **VSCode (Lomiri)** và **ChatGPT (Lomiri)**.

Trên máy mới:

```bash
cd ~/projects/lomiri-termux
bash scripts/install-work-apps.sh
bash scripts/install-shortcuts.sh
lomiri-stop
lomiri-code --no-sandbox
lomiri-chatgpt
```

VSCode trong PRoot đã thử cần `--no-sandbox`, làm giảm sandbox của Electron. Điện thoại đã cấu hình `LOMIRI_CODE_NO_SANDBOX=1` trong `config.env`; mã nguồn giữ mặc định 0 để người dùng tự chọn. Firefox dùng cấu hình sandbox mặc định. Android vẫn quản lý quyền của Termux.

Profile, extension và thư mục code thử nằm trong `runtime/`; không nhập thông tin đăng nhập của desktop cũ. Kiểm tra nội dung trước khi chấp nhận Workspace Trust của VSCode cho thư mục thử `runtime/code-workspace`. Bạn tự đăng nhập ChatGPT trong Firefox khi cần dùng tài khoản riêng.

Broker chỉ nhận tên hai app này và khởi động chúng trong process group riêng của phiên. `lomiri-stop` đã dừng các tiến trình app/phiên được ghi nhận, giữ desktop X1 còn đáp ứng.

Để giữ sáng khi rời điện thoại: Preferences của Termux:X11 → **Screen idle timeout → Never (keep screen on)**, rồi để X11 ở phía trước. Rời X11, khóa bằng nút nguồn hoặc đổi lại **System** để điện thoại nghỉ. Luôn sáng tốn pin hơn, nên cắm sạc khi để lâu.

## Trạng thái và giới hạn

- Đã thấy shell, launcher/drawer, app Qt/Wayland và nhập chữ trong phiên bình thường, không tải QML chẩn đoán.
- Người dùng đã xác nhận chạm nút và nhập chữ đều hoạt động bằng thao tác trực tiếp trên điện thoại.
- Đã dừng X server riêng, khởi động lại và gọi start hai lần mà không tạo phiên trùng; `:1` vẫn kết nối được.
- Ba test bảo vệ danh tính tiến trình đã qua. Test Qt thật kiểm tra press/release, tọa độ có phần thập phân và việc giữ nguyên các receiver khác; bỏ bản vá thì test tái hiện lỗi mất click.
- Có bridge đồng bộ cửa sổ Mir với kích thước X11 bằng sự kiện, kiểm chứng bằng Xvfb cả viewport, cửa sổ khác và state cũ. Đã đóng task Android cũ trùng tag làm sai cửa sổ hiển thị; script thống nhất URI có scheme. Rotation/layout đầy đủ và dùng lâu vẫn cần đánh giá.
- Một số chuỗi phím/chạm tự động quá nhanh bị mất dưới software rendering; giảm tốc độ đã hoàn tất thử nghiệm. Chưa xác nhận độ tin cậy của mọi kiểu nhập trong các app desktop.
- Chưa kiểm chứng nhập tiếng Việt có dấu, gesture/scroll đầy đủ hoặc launcher mở mọi app qua systemd user services.
- Render bằng CPU llvmpipe; chưa tối ưu GPU và pin. Đây là PoC Lomiri, chưa phải Ubuntu Touch hoàn chỉnh hay desktop làm việc ổn định.

Nhật ký kiểm chứng và chi tiết kỹ thuật ở `docs/`.

## Bản vá input và phát triển

QtMir gửi mouse event tới QObject `QtEventFeeder`; sự kiện không tới QWindow của shell. Thư viện preload riêng chuyển các mouse event của đúng lớp đó tới QWindow và giữ nguyên đường xử lý của đối tượng khác. Không thay Qt hệ thống.

Thư viện dùng private ABI Qt5. Khi Qt/QtMir đổi phiên bản, startup sẽ từ chối thư viện cũ. Build lại trên điện thoại rồi restart:

```bash
cd ~/projects/lomiri-termux
bash scripts/build-input-compat.sh
lomiri-stop
lomiri-start
```

Nếu thiếu compiler/headers, dùng `bash scripts/build-input-compat.sh --install-deps`.

Kiểm tra phiên/log:

```bash
lomiri-status
tail -n 60 ~/projects/lomiri-termux/runtime/session.log
cd ~/projects/lomiri-termux
python tests/session-lifecycle.py
```

`runtime/` và `config.env` không đưa vào Git hoặc ZIP mã nguồn. Các biến truyền trên dòng lệnh được ưu tiên hơn cấu hình. Mặc định tắt `LOMIRI_INPUT_TRACE`; chỉ bật khi chẩn đoán. Lệnh thử nested vẫn là `desk` rồi `bash scripts/start.sh`.

Tạo lại trên một bộ Termux đã có PRoot-Distro và Termux:X11:

```bash
cd ~/projects/lomiri-termux
bash scripts/install-debian.sh
bash scripts/install-demo-deps.sh
bash scripts/build-input-compat.sh --install-deps
bash scripts/install-shortcuts.sh
lomiri-start
```

Sau khi cài shortcut trên máy mới, mở Termux:Widget, bấm **Create shortcuts** và **Refresh widgets**. Cài distro dùng image Debian chính thức và kho APT của distro; không trộn kho Debian vào Ubuntu.

## Nguồn

- [Lomiri](https://gitlab.com/ubports/development/core/lomiri)
- [QtMir](https://gitlab.com/ubports/development/core/qtmir)
- [QtMir source tương ứng package đã thử](https://gitlab.com/ubports/development/core/qtmir/-/blob/ea2f477/src/platforms/mirserver/qteventfeeder.cpp)
- [Lomiri trong Debian](https://packages.debian.org/trixie/lomiri)
- [Termux:X11](https://github.com/termux/termux-x11)
- [PRoot-Distro](https://github.com/termux/proot-distro)
