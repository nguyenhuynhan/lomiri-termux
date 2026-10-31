# Nghiên cứu hiệu năng UI trên Snapdragon 8 Elite

Đây là báo cáo trước thí nghiệm. Xem [kết quả thử GPU](gpu-results-20261031.md)
cho renderer, số đo và các giới hạn đã kiểm chứng sau đó.

Ngày đối chiếu: 30/10/2026. Phạm vi: Lomiri trong Debian PRoot trên OnePlus 13,
Mir/QtMir, Termux:X11 và các app Wayland. Đây là kết quả kiểm tra hiện trạng và
đề xuất thí nghiệm; chưa cài driver GPU, đổi cấu hình hay restart phiên đang dùng.

## Kết luận

Phiên hiện tại chưa dùng Adreno để rasterize shell: Lomiri bị ép dùng Mesa
llvmpipe. Settings và app launcher cũng ép software rendering; VSCode thêm
`--disable-gpu` và terminal đặt GPU acceleration thành `off`.
Đây là nguyên nhân có bằng chứng của việc chưa khai thác GPU, nhưng chưa có phép
đo frame time để quy toàn bộ hiện tượng giật/chậm cho nguyên nhân này.

Hai hướng đáng thử là VirGL qua driver Android và Mesa/Freedreno KGSL trực tiếp
trong guest. Dùng VirGL làm phép thử tương thích ban đầu; đánh giá KGSL trực tiếp
để tìm hiệu năng tốt hơn sau đó. Nếu chỉ làm một thí nghiệm chuyên sâu để tìm
trần hiệu năng, ưu tiên guest thử riêng với Freedreno KGSL. Cả hai cần kiểm tra
EGL và buffer của Mir, không chỉ kết quả `glxinfo` hoặc benchmark OpenGL.

## Bằng chứng từ điện thoại đang chạy

Các lệnh đọc qua ADB và môi trường Termux hiện có; không đóng/mở app người dùng.

| Thành phần | Kết quả đọc trực tiếp |
| --- | --- |
| SoC / GPU | `SM8750`; `/sys/class/kgsl/kgsl-3d0/gpu_model`: `Adreno830v2` |
| Android | 17; security patch 2026-09-01 |
| GPU device | `/dev/kgsl-3d0` tồn tại; Termux có quyền đọc/ghi theo `os.access` |
| Guest | Lomiri 0.5.0-2; QtMir 0.8.0~git20250407.ea2f477-1+deb13u1 |
| Qt / Mesa guest | Qt Quick 5.15.15+dfsg-3; Mesa 25.0.7-2+deb13u1 |
| Mesa host | Termux Mesa 26.2.5; bản host không thay thư viện Mesa đang dùng trong Debian |
| X display | `:2`, 672 × 1339; XRandR mode khoảng 59.84 Hz, không phải FPS đo được |
| GLX / EGL X11 probe | `llvmpipe (LLVM 19.1.7, 128 bits)`; GLX báo `Accelerated: no` |
| Lomiri process | `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER=llvmpipe`, `QSG_RENDER_LOOP=basic`, `QT_QPA_PLATFORM=mirserver` |
| Thư viện Lomiri | Maps xác nhận libEGL Mesa, libLLVM 19.1 và libgallium 25.0.7 của guest |
| Settings process | `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER=llvmpipe`, Qt Wayland |
| VSCode process | Command line có `--disable-gpu`; child gpu-process có `--use-gl=disabled` |
| VSCode terminal | `terminal.integrated.gpuAcceleration` hiện là `off` |
| GPU bridge | Chưa cài `virglrenderer-android`, `angle-android`, `mesa-vulkan-icd-freedreno`, `vulkan-loader-android`; chưa có `vulkaninfo` |
| Host Vulkan ICD đã thấy | `lvp_icd.aarch64.json`, trỏ tới lavapipe CPU |
| Android EGL/GLES probe từ Termux | EGL 1.5 vendor Android; GL vendor Qualcomm; renderer `Adreno (TM) 830`; OpenGL ES 3.2 driver `V@0800.80.1`, build date 09/28/26 |

Quyền mở node KGSL là điều kiện thuận lợi, chưa chứng minh các ioctl, driver và
buffer sharing cần thiết đều hoạt động. Các counter GPU busy/frequency trong
sysfs bị từ chối quyền đọc; chưa đo GPU utilization hoặc pin.
Probe Android dùng libEGL/libGLESv2 hệ thống, tạo context và pbuffer 16×16 trong
process riêng rồi giải phóng. Kết quả xác nhận môi trường Termux có thể tạo
context GLES qua driver Qualcomm thật; chưa đo tốc độ render và chưa chứng minh
VirGL, ANGLE hoặc Mir sẽ dùng được cùng đường đó.
Một mẫu CPU Lomiri dài 3 giây cho 0% trong khoảng lấy mẫu, không có workload
animation được kiểm soát; không dùng số đó làm kết luận về hiệu năng khi thao tác.

Log khởi động Mir trong phiên hiện tại ghi:

```text
Selected rendering driver: mir:egl-generic (version 2.20.2)
Failed to bind EGL Display to Wayland display, falling back to software buffers
EGL display doesn't support EGL_WL_bind_wayland_display
Enabled linux-dmabuf import support
```

`mir:egl-generic` là tên backend, không phải bằng chứng GPU đang được sử dụng.
Thông báo bật dmabuf import cũng chưa chứng minh một app đang thực sự gửi buffer
GPU mà Mir import được. Khi đổi renderer phải kiểm tra các đường này lại.

## Các điểm ép CPU trong mã

SHA256 của năm script chính bên dưới đã đối chiếu khớp giữa workspace và phone.

| Nơi | Hành vi / thay đổi cần thiết cho thí nghiệm |
| --- | --- |
| `scripts/common.sh`, `config.env.example` | Mặc định `LOMIRI_SOFTWARE_RENDERING=1`; giữ làm fallback |
| `scripts/guest-session.sh` | Ép llvmpipe khi software=1; luôn ép render loop `basic` |
| `scripts/guest-app-services.py` | Ghi đè môi trường mọi app sang llvmpipe; Code luôn có `--disable-gpu` |
| `scripts/guest-settings.py` | Ghi đè lại llvmpipe khi chạy Settings |
| `scripts/prepare-host-shell.py` | Đặt mặc định terminal GPU `off` qua `setdefault`; không ghi đè lựa chọn người dùng đã lưu |
| `scripts/graphics-probe.sh` | Luôn ép llvmpipe; kiểm tra display mặc định `:1`, trong khi phiên direct dùng `:2` |
| `scripts/guest-demo.py` | Demo cũng ép software rendering; cần đổi theo backend khi dùng làm probe GPU |

Vì vậy, `LOMIRI_SOFTWARE_RENDERING=0` đơn lẻ không bật GPU cho toàn bộ UI.
Biến này chỉ bỏ một chỗ ép CPU và không cài hay chọn được driver Adreno.
Probe hiện có chỉ thích hợp xác nhận baseline software; cần probe chọn đúng
display và backend, in rõ renderer thực tế và fail khi fallback sang CPU.

## Đường render cần tối ưu

```text
App Qt/Electron/Firefox
  → buffer Wayland → Mir + QtMir + Lomiri
  → EGL X11 window → Termux:X11 → Android display
```

GPU cho bước hiển thị cuối của Android không đồng nghĩa shell Linux hoặc
ứng dụng đã dùng GPU. Cần kiểm chứng riêng renderer của shell, renderer của app,
buffer transport và việc present ra màn hình.
Ngay cả khi shell dùng GPU, app còn render CPU hoặc phải readback/upload buffer
cũng có thể khiến scroll và đổi cửa sổ chậm.

### A. VirGL qua Android — phép thử tương thích đầu tiên

```text
Guest Mesa virpipe → vtest socket → VirGL server trong Termux
  → EGL/GLES hoặc ANGLE → driver Android → Adreno
```

Termux có gói `virglrenderer-android`; build recipe hiện tại dùng `angle-android`
và cung cấp `virgl_test_server_android`. APT cache trên máy có candidate
1.3.0-1; ANGLE candidate 2.1.24923-f09a19ce-2. Việc có package chưa chứng minh
ANGLE sẽ chọn backend GPU nào trên máy này.

Ưu điểm: tận dụng driver Android và có thể giữ Mesa guest hiện có.
Hạn chế: thêm IPC/API translation, giới hạn extension và vấn đề EGL/Wayland.
Phải xác nhận Mesa guest có đường virpipe/vtest tương ứng và server thật sự dùng
Adreno, thay vì software backend bên dưới.

Thí nghiệm: server riêng, socket riêng nếu binary hỗ trợ, lệnh guest chọn
`GALLIUM_DRIVER=virpipe`, bỏ các biến ép llvmpipe. Xác nhận option socket qua
`--help` của đúng binary trước khi dùng. Không chiếm hoặc dừng server GPU của
desktop khác. Cần probe EGL X11, Wayland client và Mir bên cạnh GLX.
Native EGL/GLES probe trên chính máy đã qua với renderer Adreno 830; đây là
bằng chứng thuận lợi để ưu tiên thử cầu Android, vẫn cần kiểm tra server thực tế.

Nguồn: [Termux build recipe](https://github.com/termux/termux-packages/blob/master/packages/virglrenderer-android/build.sh).

### B. Freedreno KGSL trong Debian — hướng tìm hiệu năng tốt hơn

```text
Guest OpenGL/GLES → Freedreno với backend KGSL → /dev/kgsl-3d0 → Adreno
```

Maintainer của `mesa-for-android-container` công bố hỗ trợ GL/GLES/Vulkan cho
Adreno 830, build cho Debian trixie ARM64 và thử PRoot trên một máy Snapdragon
8 Elite khác. Đây là bằng chứng khả thi của driver trong container, chưa phải
kiểm chứng OnePlus 13 hoặc Lomiri của dự án.

Hướng này bỏ cầu VirGL và có thể bỏ Zink khi dùng Freedreno OpenGL trực tiếp;
lợi ích hiệu năng là giả thuyết cần đo. Chọn bản build KGSL có hỗ trợ A830 và
đúng ABI Debian/glibc. Host Termux dùng Bionic: không đưa tùy tiện thư viện host
vào `LD_LIBRARY_PATH` của guest.

Repo yêu cầu bản 26.3.0+ cho tính năng mới/A8xx; bản phát hành đã đọc là
27.0.0-devel-20261025. Không chọn các gói Debian 25.0.7 cũ chỉ vì tên distro
khớp. Bản mới là development build; cần pin artifact/checksum và thử trong
guest clone hoặc prefix thư viện riêng đủ dependency. Hướng dẫn upstream có
bước overwrite thư viện hệ thống; không áp dụng trực tiếp vào guest đang dùng.

Loader trong build này dùng `MESA_LOADER_DRIVER_OVERRIDE=kgsl`. Sau probe GL/GLES
phải thử EGL X11, buffer Mir, client Wayland, resize/IME và input bridge QtMir.
Nếu phải nâng Qt/QtMir để tương thích, giữ mốc package và rebuild input bridge
đúng private ABI; không trộn kho Debian và Ubuntu.

Nguồn: [maintainer README](https://github.com/lfdevs/mesa-for-android-container/blob/adreno-main/.github/README.md),
[release đã đối chiếu](https://github.com/lfdevs/mesa-for-android-container/releases/tag/mesa-27.0.0-devel-20261025).

### C. Turnip + Zink — phương án bổ sung

```text
OpenGL/GLES → Zink → Vulkan Turnip có KGSL/A830 → Adreno
```

Zink chuyển OpenGL sang Vulkan; cần đúng Vulkan ICD và các feature cần thiết.
Phải xác nhận `vulkaninfo` chọn Adreno, không phải lavapipe. Guide cũ về Adreno
6xx/7xx không đủ để chọn driver cho A830. Gói Android Adrenotools cho emulator
cũng không tự trở thành ICD glibc chạy được trong Debian.

Termux cung cấp Freedreno Vulkan ICD dưới subpackage của Mesa, nhưng package
đó chưa cài trên máy và không tự thay driver trong guest. Đây là lựa chọn thử
khi đường GL KGSL trực tiếp hoặc VirGL không tương thích, không phải chỉ thêm
`GALLIUM_DRIVER=zink` vào cấu hình hiện có.

Nguồn: [Mesa Zink](https://docs.mesa3d.org/drivers/zink.html),
[Termux ICD subpackage](https://github.com/termux/termux-packages/blob/master/packages/mesa/mesa-vulkan-icd-freedreno.subpackage.sh).

## Tối ưu UI sau khi xác nhận renderer

1. **Backend thống nhất:** shell và từng app đọc cùng lựa chọn renderer; vẫn cho
   phép fallback từng app. Chỉ gỡ `--disable-gpu` của Code sau khi Wayland/EGL
   probe qua; bật lại terminal GPU riêng và xác nhận trạng thái renderer Electron.
2. **Frame pacing:** giữ `basic` làm baseline. Thử `threaded` riêng khi driver
   ổn định, vì QtMir/input shim phụ thuộc Qt5 và đường swap/vsync cần đúng.
   `basic` là render loop một luồng, không đồng nghĩa software renderer.
   Dùng `QSG_INFO=1`, `QSG_RENDER_TIMING=1` và log scenegraph trong phiên đo;
   không bật log chi tiết thường trực.
3. **Giảm workload:** so sánh blur bật/tắt bằng Settings; profile QML binding,
   texture upload, app thumbnails và animation. Chỉ sửa nơi trace cho thấy tốn
   thời gian; không quy lỗi cho dock chỉ vì dock mới được thêm.
4. **Số pixel:** đo tại 672×1339 hiện có trước. Cỡ UI (`ui-scale`) đổi kích thước
   item, không giảm số pixel render như thay độ phân giải output. Nếu giảm output
   hai chiều xuống 75%, số pixel còn 56.25%, nhưng chữ/ảnh có thể kém nét.
5. **Đường buffer:** nếu renderer đã là Adreno mà vẫn chậm, ưu tiên tìm readback,
   upload/copy và sync. Đổi toàn bộ display server chỉ đáng cân nhắc khi đã chứng
   minh đây là nút thắt; Lomiri/Mir cần tương thích riêng với backend mới.

Nguồn: [Qt 5 scene graph](https://doc.qt.io/qt-5/qtquick-visualcanvas-scenegraph.html),
[Qt 5 performance](https://doc.qt.io/qt-5/qtquick-performance.html),
[Mir graphics support](https://canonical.com/mir/docs/2.21/explanation/mir-graphics-support/).

## Phép đo và tiêu chí chọn cấu hình

- Baseline llvmpipe; sau đó VirGL, KGSL trực tiếp và Zink nếu cần. Giữ cùng độ
  phân giải, blur, bộ app, độ sáng, trạng thái sạc và nhiệt độ ban đầu.
- Đo riêng mở drawer, vuốt đa nhiệm, đổi Mobile/PC, xoay màn hình, mở IME,
  scroll file Code và scroll một trang browser đã tải. Không dùng thời gian chờ
  mạng/AI hoặc lần mở extension đầu tiên để đo GPU.
- Warm up trước; chạy nhiều lượt, báo median/p95 frame interval, missed frames,
  CPU của shell/app/X11, bộ nhớ và nhiệt độ. Mục tiêu ban đầu là frame pacing
  ổn định quanh 60 Hz, khoảng 16.7 ms mỗi frame, theo output hiện tại.
- Qt frame submission không bằng Android actual presentation. Kết hợp trace Qt/Mir
  với Android frame/presentation trace nếu quyền cho phép, rồi thử bằng tay.
  Nếu không đọc được GPU counter, ghi rõ giới hạn và dùng renderer/trace làm
  bằng chứng; không suy utilization từ tên process `gpu-process`.
- Chỉ chọn làm mặc định khi renderer đã được xác nhận, UI/app tốt hơn baseline,
  không hỏng click/keyboard/rotation, và đã thử chạy liên tục 15–30 phút để xem
  throttling. Pin/video decode cần phép đo riêng.
- Thử trên display/guest riêng, snapshot cấu hình và phiên bản trước; process
  GPU server thuộc nhóm tiến trình dự án, kiểm tra identity khi dừng. Giữ Android,
  XFCE `:1`, mobile-ubuntu và app đang làm việc. Chưa cần root hay mở bootloader.

## Thứ tự thực hiện đề xuất

1. Chuẩn bị probe chọn backend/display và thu baseline animation có kiểm soát.
2. Thử VirGL trên display thử riêng để kiểm chứng đường driver Android → guest.
3. Thử KGSL/Freedreno A830 trong guest riêng với artifact đã pin, không ghi đè
   stack Debian hiện có; đối chiếu cả EGL/Mir/Wayland và frame time với VirGL.
4. Tích hợp backend tốt hơn vào shell/app launcher/Settings/demo; giữ software
   fallback. Bật GPU Code/terminal và thử threaded/blur lần lượt.
5. Chọn mặc định sau phép đo thực tế. Chưa có căn cứ hứa mức tăng FPS hay giảm pin.
