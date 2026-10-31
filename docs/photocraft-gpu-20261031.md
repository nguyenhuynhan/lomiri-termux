# PhotoCraft dùng Adreno bên trong Lomiri — 31/10/2026

PhotoCraft 0.18.0 đã chạy bằng Vulkan/Adreno và hiển thị ảnh bên trong
**phiên Lomiri chính đang chạy**, trên Termux:X11 `:2`, tag `lomiri-poc`.
Không restart Lomiri. Đã mở PNG mẫu 256×256, vẽ nét và phóng lên 200%; ảnh
Android chụp lại xác nhận cả gradient và nét vẽ được present đúng.

## Cách mở

Chọn **PhotoCraft** trong menu Lomiri, hoặc chạy `lomiri-photocraft` trong
Termux. Desktop entry mới có tên **PhotoCraft (GPU)**; drawer của phiên hiện
tại vẫn cache tên cũ **PhotoCraft**, nhưng đã thử mở lại app qua chính mục đó
và xác nhận driver Vulkan riêng được nạp. Không cần restart để dùng GPU.

Nút **Open** bên trong ArtCraft Launcher vẫn chạy AppImage trực tiếp và kế
thừa cấu hình GL/CPU của Launcher. Muốn dùng GPU, mở qua Lomiri như trên.
Không sửa binary AppImage chính thức hoặc đổi renderer cho mọi Craft apps.

Cài lại launcher từ project:

```bash
bash scripts/install-photocraft-gpu.sh
```

Script không cài package, không đổi thư viện Mesa hệ thống và không điều
khiển vòng đời shell. Nó cần PhotoCraft và driver riêng đã có trên điện thoại.
Launcher ghim bản **0.18.0 đã thử**; nâng phiên bản cần kiểm chứng lại trước
khi đổi đường executable/checksum. ArtCraft cập nhật desktop entry có thể
ghi đè `Exec`; nếu xảy ra, chạy lại script trên để khôi phục entry riêng.

## Nguyên nhân và đường sửa

Ban đầu adapter/ArtCraft đặt `LIBGL_ALWAYS_SOFTWARE=1`,
`GALLIUM_DRIVER=llvmpipe`, `WGPU_BACKEND=gl`. Log PhotoCraft trước sửa ghi
`softwareAdapter` và `all documents: CPU`, với adapter Mesa llvmpipe.

Wrapper riêng bỏ cờ ép CPU, chọn `WGPU_BACKEND=vulkan` và
`WINIT_UNIX_BACKEND=wayland`. ICD riêng trỏ tới `libvulkan_freedreno.so`
trong `runtime/gpu-experiments/kgsl-root/usr/lib/aarch64-linux-gnu`.
Driver Mesa 27.0.0-devel tại commit `eb3e7fd4f0` là artifact đã kiểm tra trong
[báo cáo GPU](gpu-results-20261031.md), không ghi đè `/usr/lib`.

`MESA_VK_WSI_DEBUG=sw` chọn đường Wayland shared-memory presentation của
driver Vulkan. GPU vẫn dựng canvas; buffer được đọc/chuyển cho compositor
software của Lomiri qua `wl_shm`, tránh đường import dmabuf từng làm QtMir/Mir
crash trong phép thử client GL trước đây. Cờ `sw` ở đây áp dụng cho WSI;
không chọn llvmpipe làm physical device.

```text
PhotoCraft → Vulkan / Adreno 830 → buffer SHM → Mir/Lomiri software
           → X11 :2 → Termux:X11 → màn hình Android
```

Source đã đối chiếu đúng commit:
[wsi_common.c](https://github.com/lfdevs/mesa-for-android-container/blob/eb3e7fd4f0/src/vulkan/wsi/wsi_common.c)
và
[wsi_common_wayland.c](https://github.com/lfdevs/mesa-for-android-container/blob/eb3e7fd4f0/src/vulkan/wsi/wsi_common_wayland.c).

## Kiểm chứng

- AppImage `photocraft-0.18.0-linux-aarch64.AppImage`: 113687048 byte;
  SHA256 `ce3002bb8c5e6b783ac6a2d9c1cd033e08fb9ad5e7d75cd3da4d0c9bedbdc5ff`.
  Setup kiểm tra checksum của binary đã thử trước khi đăng ký.
- Vulkan physical-device probe với ICD riêng báo `Adreno (TM) 830v1`, vendor
  `0x5143`, device ID `0x44050001`, loại integrated GPU.
- Hai probe X11 riêng `:4` giữ app chạy trong 30 giây và khởi tạo canvas GPU.
  Đây là bước chẩn đoán; giải pháp đã triển khai vẫn dùng Wayland trong Lomiri.
- Bản sao software Lomiri trên `:3` chạy PhotoCraft Vulkan/SHM qua UAL.
  Ảnh Android xác nhận PNG, nét vẽ và zoom; shell không crash. Một lần chụp
  trước đó hiện “Not connected”; chỉ những ảnh chụp sau khi nối lại server
  thử mới được dùng làm bằng chứng presentation.
- Phiên chính mở qua `lomiri-photocraft`: UAL trả
  `Started: ai.storyteller.photocraft`, app PID 21542/PGID 15959. Process maps
  có private `libvulkan_freedreno.so`, fd có `/dev/kgsl-3d0`. Log khởi tạo
  `gpu_canvas`, dùng `WGPU_BACKEND=vulkan`; PNG mẫu có `on the gpu path` và
  `refresh gpu-full 65536 px`. Không có softwareAdapter warning trong lần mở
  mới này. Màn hình trống có thể ghi `cpu path` với `refresh none 0 px`;
  dòng đó không phải kết quả render ảnh mẫu.
- Trong phiên chính, mở mẫu qua Open/Zenity, vẽ nét và zoom 200% thành công.
  File chooser portal chưa có interface cần thiết; app fallback sang Zenity
  và mở ảnh được. Đóng ảnh thử, bỏ thay đổi mẫu, thoát PhotoCraft bình thường
  rồi mở lại qua tile PhotoCraft trong drawer để kiểm tra đường menu.
- Shell Lomiri PID **16241**, start time **26533099**, giữ nguyên trong
  kiểm tra và triển khai. ArtCraft/phiên shell được giữ. Các PID chỉ là snapshot.
- Wrapper đăng ký atomically vào `runtime/app-catalog.json`; adapter đang
  chạy đọc danh mục mỗi lần mở. Không nới whitelist môi trường/tham số UAL.
- Phiên thử `:3` đã dừng qua supervisor có PID/start time/PGID/command path
  khớp. Không dùng `killall`/`pkill`; đưa Android về `lomiri-poc`.
- Python compile và Bash syntax checks của các launcher mới đã qua.

Ảnh kiểm chứng ngoài Git trong workspace:
`artifacts/photocraft-lomiri-gpu-input.png` (bản sao),
`artifacts/photocraft-primary-gpu-input.png` (phiên chính).
Log trên phone: `runtime/app-ai.storyteller.photocraft.log` và
`runtime/gpu-software/runtime/app-ai.storyteller.photocraft.log`.

## Giới hạn và hoàn tác

Đây là GPU rendering kèm copy/readback qua CPU để present trong shell
software. Chưa chứng minh zero-copy, mọi thao tác/layer/PSD đều chạy GPU,
hiệu năng ảnh lớn, pin, nhiệt, tiếng Việt trong PhotoCraft hay ổn định dài hạn.
Slow-frame log của ảnh mẫu vẫn có thời gian xử lý CPU đáng kể; không suy ra
mức tăng tốc/FPS từ việc tạo được GPU canvas.

Setup giữ profile PhotoCraft hiện có. Chỉ các phép thử riêng dùng profile
rỗng; không đọc/lưu credential hay cache đăng nhập. Bộ gõ của phiên chính
được tạm đóng khi nhập đường file mẫu, rồi trả về trạng thái active ban đầu.

Muốn trở về đường CPU: lưu việc và đóng riêng PhotoCraft; khôi phục desktop
entry từ `runtime/photocraft-gpu/original-photocraft.desktop`, xóa riêng record
`ai.storyteller.photocraft` khỏi `runtime/app-catalog.json` bằng ghi atomic.
Danh mục sẽ lại phát hiện AppImage chính thức với `CRAFT_ENV` GL/llvmpipe.
Không cần dừng shell hoặc xóa driver/profile để hoàn tác.

Không commit, push hoặc publish.
