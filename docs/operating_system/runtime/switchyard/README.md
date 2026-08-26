# Patched Switchyard Runtime

Private runtime provenance for the decision-evidence integration.

- Upstream: `https://github.com/NVIDIA-NeMo/Switchyard`
- Base tag: `v0.2.0`
- Base commit: `1fc9ab887d1c663b0048ae24d5f473d15ed8daaa`
- Local patch: `decision-evidence.patch`
- Patch SHA-256: `70a16653f171ceb91b4f0ef5f60f679ad0ab0531262c98ae0fefc1f701ede179`

## Rebuild

```bash
git clone https://github.com/NVIDIA-NeMo/Switchyard.git
cd Switchyard
git checkout 1fc9ab887d1c663b0048ae24d5f473d15ed8daaa
git apply /path/to/project-OS-starter/docs/operating_system/runtime/switchyard/decision-evidence.patch
cargo install --path crates/switchyard-server --locked --force
```

## Compatibility smoke

Run without credentials or provider traffic:

```bash
switchyard-server --version
switchyard-server --config "$HOME/.switchyard/routes.toml" --dry-run
```
