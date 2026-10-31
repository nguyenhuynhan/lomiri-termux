# Lomiri trên Termux

[English guide](README.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

Lomiri thật đã chạy trực tiếp trên OnePlus 13 qua Termux:X11. **Không cần mở XFCE trước.** Dự án trên điện thoại: `~/projects/lomiri-termux`.

Phiên dùng Debian trixie ARM64 trong container riêng `lomiri-debian`: Lomiri 0.5.0, Mir 2.20.2, QtMir 0.8.0~git20250407. Android tiếp tục quản lý điện thoại; Ubuntu `mobile-ubuntu` và bộ công cụ code hiện có dùng riêng.

## Mở và dừng

Trên điện thoại hiện tại, chạm biểu tượng **Lomiri** ở màn hình chính, ngay dưới Termux:X11, để mở trực tiếp. Khi ghim trên máy mới: mở bộ chọn shortcut của **Termux:Widget**, chọn **Lomiri** ở thư mục đầu tiên rồi bấm **Thêm**. Cho phép Termux:Widget tạo lối tắt và cho phép Termux **Hiển thị trên ứng dụng khác** nếu Android yêu cầu. Shortcut **Stop Lomiri** dừng riêng phiên thử.

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

Trong **Hello Lomiri**, chạm nút để tăng số; chạm ô nhập để thử bàn phím. App là Qt/Wayland client thật trong shell. Nút hình bàn phím của Termux:X11 vẫn mở/đóng thủ công.

Ngày 31/10/2026, cấu hình thử trên OnePlus 13 dùng **Unexpected Keyboard 2.1.0
ở English + Fcitx5/UniKey Telex trong Debian**. Chạy `bash scripts/install-keyboard.sh`
để cài phần Linux trên máy mới, chọn Unexpected trong Android, lưu công việc rồi
khởi động lại Lomiri. Trong Session Settings bật **Tự hiện bàn phím** và **Tiếng Việt**;
nút **VN/EN** trên dock đổi bộ gõ. Không dùng Ctrl+Space vì Android dùng nó để đổi IME.

Chạm tự mở, gõ dấu và Backspace liên tiếp đã qua thử ADB trong Qt, Terminal,
VSCode, ChatGPT Desktop và Firefox. Drawer/search của Lomiri chỉ nhập English,
có thể cần mở bàn phím thủ công. Người dùng đã xác nhận trực tiếp cả tự mở,
đúng dấu và Backspace trong Thử bàn phím. Xoay và gõ nhanh/dùng lâu còn cần kiểm chứng.
Xem [báo cáo bàn phím](docs/keyboard-20261031.md).

Bản vá input riêng cho dự án đã làm click và nhập chữ hoạt động trong các phép thử. Đã kiểm tra cả X11 click/type và thao tác qua Android, gồm phím trên Gboard. Ngày 24/10/2026, người dùng thử trực tiếp trên OnePlus 13 và xác nhận “Chạm và nhập đều được”. Một số lần chạm ADB cực ngắn không được ghi nhận; độ ổn định khi dùng lâu vẫn cần đánh giá.

## ArtCraft và PhotoCraft GPU

Cài ArtCraft Launcher ARM64 trong Debian riêng bằng
`bash scripts/install-artcraft.sh`; mở từ menu **ArtCraft Launcher** hoặc
`lomiri-artcraft` trong Termux. Các Craft apps cài qua AppImage được nhận diện
trong catalog đọc mỗi lần mở, không cần restart shell khi thêm app.

PhotoCraft 0.18.0 đã thử Vulkan/Adreno bên trong Lomiri software trên OnePlus 13.
Với private driver đã chuẩn bị theo báo cáo GPU, chạy
`bash scripts/install-photocraft-gpu.sh`, rồi mở **PhotoCraft** trong menu Lomiri
hoặc `lomiri-photocraft`. GPU dựng ảnh; shared-memory presentation chuyển khung
cho shell software. Nút Open trong ArtCraft còn dùng cấu hình CPU cũ.

Xem [ArtCraft](docs/artcraft-20261031.md) và
[PhotoCraft GPU](docs/photocraft-gpu-20261031.md) về checksum, cách dùng,
kiểm chứng ảnh/vẽ/zoom và giới hạn hiệu năng/pin.

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

## Bổ sung ngày 30/10/2026

Menu Lomiri đã mở được bộ app cơ bản qua adapter của phiên PRoot. Cài phần bổ sung trên máy mới bằng `bash scripts/install-core-apps.sh`, rồi restart Lomiri. Bộ app gồm Terminal, File Manager, Calculator, Clock, Calendar, Gallery và Media Player; VSCode/Firefox được cài riêng như hướng dẫn ở trên.

Shortcut và menu dùng cùng cơ chế mở app. Khi VSCode đang chạy, chọn icon của nó để chuyển về cửa sổ hiện có. Rotation do Android thực hiện; overlay riêng theo kích thước màn hình và tránh xoay hai lần. VSCode dùng hộp thoại file tích hợp và Python mặc định `/usr/bin/python3` trong guest.

Ở phiên direct, dock luôn hiện ngang ở cạnh dưới, kể cả khi app toàn màn hình. Chạm nút chín chấm bên trái để mở danh sách ứng dụng; chạm icon để mở/chuyển app. Dấu bên dưới icon cho biết app đang chạy, màu cam là app được chọn. Dock bám theo cạnh dưới khi xoay máy; nếu nhiều icon, vuốt ngang trên hàng icon. Vùng app được thu ngắn để không bị dock che.

Nút **Mobile / PC** ở mép phải dock hiển thị chế độ hiện tại; chạm để đổi ngay, giữ các app đang chạy. Lựa chọn được lưu trong cấu hình riêng của phiên và giữ nguyên khi xoay máy. Mobile dùng app phủ vùng làm việc; PC có cửa sổ, thanh tiêu đề và nút **đóng / thu nhỏ / phóng to hoặc khôi phục**. Khi app phóng to hoặc F11 trong PC, các nút nằm ở góc trên bên trái.

Để đóng app ở Mobile: chạm biểu tượng **hai cửa sổ chồng nhau** cạnh nút Mobile/PC để mở đa nhiệm, tìm thẻ app rồi **vuốt thẻ lên trên**. Có thể vuốt ngang để tìm app khác; chạm thẻ để quay lại app. Đổi sang app khác bằng dock chỉ chuyển cửa sổ, không đóng app cũ. App có thể hỏi lưu nội dung trước khi đóng.

Đã thử tạo/lưu/chạy Python trong VSCode và kết nối audio tới Termux. Laban Key còn lỗi Backspace; cấu hình Unexpected + UniKey mới đã qua phép thử tiếng Việt/xóa chữ trong các app nêu trên. Media, báo thức, dịch vụ phần cứng và độ ổn định dài hạn chưa được coi là hoàn thiện. Xem [báo cáo kiểm chứng](docs/verification-20261030.md) và [báo cáo bàn phím](docs/keyboard-20261031.md). Các mục dưới bao gồm cả kết quả lịch sử.

## Cài đặt phiên Lomiri

Ứng dụng **Session Settings / Cài đặt phiên Lomiri** tùy chỉnh Mobile/PC, giao diện sáng/tối, cỡ shell,
hiệu ứng làm mờ, kích thước dock, app ghim, hình nền và phím tắt. Cấu hình lưu
trong `runtime/config` của dự án. Cỡ shell không thay cỡ chữ VSCode/Firefox.
F8 mở danh sách app, F9 đổi Mobile/PC; có thể chuyển sang Ctrl+Alt+D/M trong app.
Bộ chọn hình nền duyệt ảnh trong Debian hoặc đường dẫn đã bind vào guest.

Khi cập nhật mã trên điện thoại, lưu việc trước rồi `lomiri-stop`, `lomiri-start`.
Settings được thêm vào dock một lần, giữ các app ghim hiện có. Trên máy mới chạy
`bash scripts/install-core-apps.sh` trước. Wi‑Fi, Bluetooth, độ sáng, âm lượng và
quyền ứng dụng chỉnh trong Cài đặt Android.

Xem kiểm chứng và các phần còn chờ thử ở [báo cáo Settings](docs/settings-20261030.md).

**System Settings** là ứng dụng gốc Lomiri, có icon riêng trong menu và dock.
Đã khôi phục launcher, nối hình nền và kích thước dock với cấu hình phiên, cùng
bản vá null khi đổi theme. Để dựng frontend gốc có bản vá trên máy mới, chạy
`bash scripts/build-native-settings.sh` rồi restart Lomiri. Các dịch vụ phần cứng
Android chưa được nối đủ; xem [báo cáo app gốc](docs/native-settings-20261030.md).

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
