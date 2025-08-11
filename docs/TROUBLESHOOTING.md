## Troubleshooting

### RealSense not found / permission errors
- Install udev rules: `bash scripts/install_realsense_udev.sh`
- Replug device or reboot.
- Verify: `rs-enumerate-devices` should list your D435.

### `ModuleNotFoundError: pyrealsense2`
- Ensure `python3-pyrealsense2` is installed via apt or built from source.
- The app attempts to import from common system paths if venv misses it.

### Torch GPU not available
- Install Jetson-compatible torch/vision via Jetson AI Lab index (see INSTALL.md §4), or install wheel files offline.
- Verify: `python -c "import torch; print(torch.cuda.is_available())"` must be True.

### OpenCV GUI errors (no DISPLAY)
- The app disables preview automatically when `DISPLAY` is missing.
- You can also set `output.preview_window: false` in config.

### Network push to GitHub failing
- Ensure you have at least one commit on `main` before pushing.
- Configure identity and remote:
  - `git config user.name "Your Name"`
  - `git config user.email "you@example.com"`
  - `git remote set-url origin <URL>`
  - `git push -u origin main`

### KUKA EKI XML schema mismatch
- Adapt tags/structure in `src/output/eki_sender.py` or your controller EKI config to match.


