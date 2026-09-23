#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 patch_features.py
python3 patch_visual.py
python3 patch_content_core.py
python3 patch_parental.py
python3 patch_v14_settings.py
python3 patch_v14_accounts.py
python3 patch_v15.py
python3 patch_v2_scope.py
python3 patch_v2_search.py
python3 patch_v2_multiscreen.py
python3 patch_v2_extras.py
python3 patch_v2_m3u.py
python3 patch_v2_zapping.py
python3 patch_v2_guide.py
python3 patch_v2_cast.py
python3 patch_player.py
python3 patch_v21_tracks.py
python3 patch_v22_clone_ui.py
python3 patch_v22_version.py
python3 patch_v23_video_clone.py
python3 patch_v23_version.py
python3 patch_v231_layout.py
python3 patch_v231_version.py
python3 patch_v24_live_media.py
python3 patch_v24_sources.py
python3 patch_v24_version.py
python3 patch_v25_control.py
python3 patch_v25_version.py
python3 patch_v26_epg_subtitles.py
python3 patch_v26_version.py
python3 patch_v27_stalker_players.py
python3 patch_v27_version.py
python3 patch_v28_tracks_automation.py
python3 patch_v28_version.py
python3 patch_v29_dvr_service.py
python3 patch_v29_version.py
python3 patch_v30_final_parity.py
python3 patch_v30_version.py
python3 patch_v31_brand.py
python3 patch_v31_version.py

echo "PIMFLEX TV release patches applied."
