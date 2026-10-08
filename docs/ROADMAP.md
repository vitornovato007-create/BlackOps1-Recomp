# Roadmap

## v0.1 — Codegen probe

- [x] Repository scaffold
- [x] ReXGlue 0.10.0 manifest
- [x] GitHub Actions workflow
- [x] Local setup helpers
- [ ] Supply user's own `default.xex`
- [ ] Run code generation
- [ ] Record first failure/success

## v0.2 — Codegen stabilization

Possible work after the first report:

- function boundaries
- import definitions
- unsupported instructions
- VMX/AltiVec handling
- generated C++ compilation

## v0.3 — Runtime

Possible work:

- Xbox 360 kernel/runtime compatibility
- memory model
- threading
- filesystem
- timing

## v0.4 — Graphics

Possible work:

- Xenos-related interfaces
- shader translation
- Vulkan backend
- Mali-G76 compatibility

## v0.5 — Android

Possible work:

- Android NDK
- ARM64
- input
- audio
- storage
- APK packaging

## v0.6+

Only after the previous stages are actually working:

- boot
- menus
- campaign
- multiplayer investigation
- performance optimization
