# Kết quả thử GPU cho Lomiri

Các phép đo menu thực hiện ngày 30/10/2026; thử bổ sung client ngày 31/10/2026.
Thiết bị: OnePlus 13, SM8750, Adreno 830. Các phiên thử dùng display `:3`,
tag `lomiri-gpu-probe`, bản sao project và cấu hình riêng. Phiên chính `:2`
giữ cấu hình software rendering.

## Kết luận

Đã chạy được shell Lomiri bằng GPU qua cả VirGL, Freedreno/KGSL trực tiếp và
Zink/Turnip. **Zink/Turnip với render loop `basic` cho kết quả tốt nhất trong
phép thử menu**, và kết quả giữ được khi lặp theo thứ tự ngược.

Phương án thử được đến hiện tại là **Zink/basic cho shell, software cho client**.
Ngày 31/10, đã tạo được EGL/Wayland context Adreno cho client qua KGSL, nhưng
Lomiri crash khi hiển thị Calculator GPU trong shell Zink. Shell KGSL thiếu
extension import cần thiết, nên Calculator lại dùng llvmpipe. VSCode đã mở được
trong phiên Zink ngày 30/10, nhưng chưa xác nhận renderer thực tế của Electron.
Chưa chuyển backend GPU thành mặc định.

## Runtime của các phép thử

OnePlus 13/PJZ110, Android 17; sysfs báo `Adreno830v2`. Debian trixie dùng
Lomiri `0.5.0-2`, Mir `2.20.2`, QtMir
`0.8.0~git20250407.ea2f477-1+deb13u1`, Qt Quick `5.15.15+dfsg-3` và Mesa
baseline `25.0.7-2+deb13u1`. Termux Mesa `26.2.5` là thư viện host riêng.
Driver Qualcomm của Android EGL/GLES probe báo `V@0800.80.1`, build 09/28/26.
Mesa thử riêng báo `27.0.0-devel (git-eb3e7fd4f0)` và renderer `Adreno 830v1`;
khác biệt chuỗi v1/v2 chưa được dùng để kết luận revision phần cứng.

## Kết quả renderer và ứng dụng ngày 30/10

| Cấu hình | GLX / EGL X11 | Shell Lomiri | Client Wayland |
| --- | --- | --- | --- |
| llvmpipe | CPU, Accelerated: no | CPU, baseline | Baseline CPU |
| VirGL / Android GLES | EGL: virgl (Adreno 830); GLX timeout 25 giây | Hiển thị shell; log Qt xác nhận virgl (Adreno 830) | Chưa kiểm chứng renderer app trong cấu hình này |
| VirGL / ANGLE GL | EGL dùng ANGLE/Adreno; GLX timeout, server có EGL_BAD_ACCESS | Chưa chọn cho thí nghiệm shell | Chưa kiểm chứng |
| Freedreno/KGSL | Accelerated: yes, GL 4.6 / GLES 3.2 | Qt xác nhận Adreno 830; menu và click hoạt động | Calculator render bằng llvmpipe; EGL Wayland không khởi tạo được |
| Zink/Turnip | Accelerated: yes, Vulkan 1.4 trên Adreno 830; GL 4.6 / GLES 3.2 | Qt xác nhận Zink/Adreno; menu hoạt động | Calculator dùng llvmpipe; VSCode hiển thị được; EGL Wayland không khởi tạo được |

Mir 2.20.2 vẫn ghi thiếu `EGL_WL_bind_wayland_display` và fallback software
buffers. Shell Zink bật linux-dmabuf import; shell KGSL ngày 31/10 không bật
được vì thiếu `EGL_EXT_image_dma_buf_import_modifiers`. Bật import chưa chứng
minh client gửi được buffer GPU tới Mir. Đây là phần cần điều tra để tăng tốc app.

## Thử client bổ sung ngày 31/10

Đã kết nối ADB lại sau khi người dùng tắt/bật Wi-Fi. Phiên chính đã dừng trước
khi bắt đầu các phép thử mới; state file cũ trỏ tới PID không còn tồn tại.

Phát hiện lỗi trong harness: đường socket Wayland của bản sao thử trên host dài
114 byte. Client chạy trong cùng lần PRoot vẫn kết nối được, nhưng probe từ lần
PRoot khác không kết nối được; do đó lỗi `eglInitialize` ngày 30/10 chưa phải
bằng chứng đầy đủ về driver. Đổi bản sao từ
`runtime/gpu-experiments/project-zink` sang `runtime/gpu-zink` giảm đường socket
xuống 94 byte. Socket xuất hiện trên host và probe từ PRoot khác kết nối được.
Không đổi đường project/phiên chính hoặc vị trí prefix driver.

| Shell / client | Kết quả bổ sung |
| --- | --- |
| Zink / Zink | EGL Wayland khởi tạo được nhưng báo `failed to create dri2 screen`, rồi dùng llvmpipe. `LIBGL_KOPPER_DRI2=true` không cải thiện |
| Zink / KGSL | EGL Wayland probe báo GL 4.6/GLES 3.2 trên Adreno 830; Calculator cũng ghi renderer Adreno. Lomiri nhận cửa sổ rồi SIGSEGV khi bắt đầu hiện surface |
| KGSL / KGSL | Shell Adreno; không bật được dmabuf import vì thiếu extension modifiers. Calculator dùng llvmpipe; chưa chứng minh GPU client presentation |
| Zink / software | Calculator hiển thị, nhập `1+2` qua X11 input và shell tiếp tục chạy đến lúc chủ động dừng. Renderer Calculator là llvmpipe. Đây là kiểm tra ngắn, chưa phải kiểm tra độ ổn định dài hạn |

Wayland registry trong shell Zink quảng bá `zwp_linux_dmabuf_v1` version 3,
không có `wl_drm` hoặc feedback main-device version 4. Đối chiếu source Mesa
đúng commit cho thấy đường khởi tạo GPU cần xử lý việc tìm device; chọn KGSL
tạo được context trên thiết bị này. Chưa kết luận chỉ riêng thiếu protocol gây
ra toàn bộ fallback hoặc crash.

Lặp lại hybrid với preload chẩn đoán xác nhận
`LOMIRI_CRASH_TRACE signal=11 address=(nil)` sau `New node`. Backtrace chỉ có
hai frame, không xác định được hàm gây lỗi. Không coi context GPU hoặc log
renderer là bằng chứng đã present được ứng dụng GPU.

Đã thêm `--client-backend inherit|kgsl|software` và `--trace-crash` cho script
thử. Với client software, bản sao giữ cờ GPU-off của Code và terminal; shell
vẫn dùng GPU. Tất cả chỉ áp dụng vào bản sao, không sửa launcher mặc định.

Source đối chiếu:
[Mesa platform_wayland.c tại eb3e7fd4f0](https://github.com/lfdevs/mesa-for-android-container/blob/eb3e7fd4f0/src/egl/drivers/dri2/platform_wayland.c).

## Phép đo menu

Workload: hai lượt đóng/mở menu để warm up, sau đó 12 lượt toggle bằng X11 input.
Output 672×1339; các phiên thử lúc này có mode khoảng 90 Hz. Cùng QML shell,
cùng thao tác và render loop `basic`, trừ hàng thử `threaded` riêng.
Thu số liệu qua `QSG_RENDER_TIMING=1`, chỉ lấy đoạn log của workload sau warm up.

**Các số dưới là thời gian Qt ghi nhận cho một vòng render, không phải FPS
hoặc thời gian presentation thực tế của Android.** Số đo có độ phân giải ms,
bao gồm overhead của logging. p95 dùng phương pháp nearest rank.

| Backend | Lượt 1 median / p95 | Lượt 2 median / p95 | Số frame được ghi, lượt 1 / lượt 2 |
| --- | --- | --- | --- |
| llvmpipe, basic | 31 / 44 ms | 30 / 45 ms | 260 / 239 |
| VirGL, basic | 22 / 41 ms | Không lặp | 269 |
| KGSL, basic | 9 / 26 ms | 8 / 32 ms | 298 / 282 |
| Zink/Turnip, basic | 4 / 16 ms | 3 / 16 ms | 357 / 356 |
| KGSL, threaded | 14 / 34 ms | Không lặp | 275 |

Thứ tự lượt 1: CPU → VirGL → KGSL → Zink; sau đó thử KGSL/threaded.
Lượt 2 đảo thứ tự: Zink → KGSL → CPU, để kiểm tra ảnh hưởng của thứ tự chạy.
Không chuyển các tỉ lệ thời gian này thành tuyên bố FPS hoặc pin.

`threaded` đã chạy được, nhưng không cải thiện phép thử này. Riêng số trên
render thread không bao gồm toàn bộ công việc của GUI thread; log còn cho thấy
swap chờ đáng kể. Giữ `basic` cho bước thử tiếp theo.

## Các thay đổi đã thực hiện

- Cài hai package Termux mới: `virglrenderer-android 1.3.0-1` và
  `angle-android 2.1.24923-f09a19ce-2`. Không nâng hoặc gỡ package hiện có.
- Tải bộ Mesa Debian trixie ARM64 vào `runtime/gpu-experiments/kgsl-root`,
  không ghi đè `/usr/lib` của Debian. Prefix này chỉ được chọn qua môi trường
  của process thử và bind riêng.
- Artifact đã pin: `mesa-for-android-container_27.0.0-devel-20261025-r1_debian_trixie_arm64.tar.gz`.
  SHA256 đã kiểm tra:
  `41414e990483010bddd088c3ee6d13bbd50b62c9de06f21896539ba2c3e8383b`.
  Mesa trong artifact báo `27.0.0-devel (git-eb3e7fd4f0)`.
- Tạo Vulkan ICD JSON riêng trỏ tới prefix thử. Không sửa ICD hệ thống.
- Bản sao project gỡ các cờ ép CPU cho app, giữ cấu hình gốc; Code thử dùng
  profile/workspace riêng và kế thừa lựa chọn no-sandbox đã có của người dùng.
- Thêm các script `gpu-probe.py`, `gpu-session.py`, `gpu-summarize.py`.
  Script từ chối display đang dùng, xác minh PID/start time/group khi dừng.
- Phát hiện hai process broker còn sót từ lần startup thất bại đầu tiên;
  đã dừng đúng PID sau khi xác minh group và command path, bổ sung cleanup cho
  trường hợp supervisor thoát sớm.
- Trước khi mất kết nối ADB, các phiên thử đã kết thúc và cửa sổ phiên chính
  đã được mở lại. Ngày 31/10 đọc lại thấy phiên chính đã dừng; không tự khởi động lại.

### Kiểm tra kết nối lại ngày 31/10

ADB `37.0.1` đã phát hiện dịch vụ `_adb-tls-connect._tcp`, nhưng kết nối TCP
timeout với lỗi Windows `10060`. Kiểm tra LAN cho thấy ARP của điện thoại ở
trạng thái `Unreachable`, ping báo `Destination host unreachable` từ máy tính.
Chưa đủ bằng chứng xác định nguyên nhân Wi-Fi/router; lỗi xảy ra trước khi
xác thực ADB. Sau khi tắt/bật Wi-Fi, ADB tự kết nối lại với key đã tin cậy.
Đã thu raw log và đọc lại trạng thái phiên chính/phiên thử. Không lưu mã ghép nối.

Cả ba script GPU đã qua kiểm tra cú pháp Python tại workspace ngày 31/10,
bao gồm các tùy chọn mới. Các phiên thử mới đã kết thúc/dừng bằng kiểm tra
identity; quét lại không còn process của bản sao cũ/mới hoặc X11 tag thử.
Điện thoại được đưa về màn hình Android Home như trước thử nghiệm.

Nguồn artifact:
[release được dùng](https://github.com/lfdevs/mesa-for-android-container/releases/tag/mesa-27.0.0-devel-20261025-r1).

## Log và chạy lại

Log, project thử, driver và JSON/CSV nằm trên phone trong
`~/projects/lomiri-termux/runtime/gpu-experiments/`. Ảnh kiểm chứng nằm trong
`artifacts/` của workspace; raw log/ảnh/driver không đưa vào Git.

Đã thu 43 file cũ vào `artifacts/gpu-logs-20261031/` và 54 file sau thử client
vào `artifacts/gpu-logs-final-20261031/`, mỗi bộ có archive và manifest SHA256.
Checksum toàn bộ file đã khớp. Chạy lại analyzer trên log cũ tại workspace cho
đúng cả 8 record trong JSON của phone. Log EGL client và ảnh ngày 31/10 nằm
riêng trong `artifacts/gpu-wayland-*-20261031.log` và `artifacts/gpu-*-20261031.png`.

Chạy trong Termux, với driver thử và dependency đã chuẩn bị:

```bash
cd ~/projects/lomiri-termux
python scripts/gpu-probe.py zink
python scripts/gpu-session.py zink --timing --exercise-menu
python scripts/gpu-summarize.py
```

Phiên tương tác có thời hạn, tách khỏi phiên chính:

```bash
python scripts/gpu-session.py zink --client-backend software --duration 300
```

Script khởi tạo cửa sổ thử và dừng sau thời hạn. Android có thể chặn việc đưa
activity lên trước từ process nền; nếu cần, mở cửa sổ tag `lomiri-gpu-probe`
của Termux:X11. Lưu việc nếu tự tạo file trong phiên thử. Các lệnh trên chưa
đổi backend mặc định của `lomiri-start`.

## Phần chưa kiểm chứng

- GPU renderer thực tế của VSCode; các lần gọi CLI `--status` không trả dữ liệu
  chẩn đoán dùng được. Có gpu-process hoặc không có `--use-gl=disabled` chưa đủ
  để xác nhận hardware rendering.
- GPU buffer presentation cho app Wayland; hybrid crash chưa xác định được
  hàm gây lỗi. Firefox/WebGL, Settings và các app khác chưa có kết quả GPU
  renderer trong các phiên thử này.
- Scroll/editor workload, tiếng Việt/IME, rotation và đa nhiệm trên backend GPU
  chưa có bộ kiểm chứng đầy đủ.
- Android presentation trace, pin, GPU busy và thermal throttling dài hạn.
  Counter GPU sysfs bị từ chối quyền đọc trong lần audit trước.

Bước tiếp theo là điều tra crash lúc QtMir/Mir nhận surface GPU và extension
import của KGSL. Giữ Zink/basic + client software làm cấu hình thử dùng được
trong kiểm tra ngắn; kiểm chứng workload ứng dụng và thao tác thực tế trước
khi đổi mặc định. KGSL/basic là ứng viên dự phòng cho shell.
