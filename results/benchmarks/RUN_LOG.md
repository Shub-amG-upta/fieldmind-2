# Benchmark run log

One line per event, laptop time. Written by `scripts/benchmark.sh`; never rewritten.

| time | test | event | details |
|---|---|---|---|
| 2026-10-19 13:59:55 | bevideas_shadow | batch_start | command=scripts/benchmark.sh bevideas_shadow dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=shadow,first=shadow,actions=shadow,unknown=shadow,verifier=shadow,notes=shadow,clear_skip=shadow; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=shadow,first=shadow,actions=shadow,unknown=shadow,verifier=shadow,notes=shadow,clear_skip=shadow", "bev_device": "npu"} |
| 2026-10-19 14:00:13 | bevideas_shadow | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=36.0 |
| 2026-10-19 14:02:42 | bevideas_shadow | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=141.6; group_top1=0.561; calls=31; unusable=0; bev_ideas={"actions": {"calls": 14, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 23, "failed": 0, "rejected": 0, "used": 0}, "notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 57, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:06:05 | bevideas_shadow | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=39.7 |
| 2026-10-19 14:09:35 | bevideas_shadow | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=201.1; group_top1=0.625; calls=51; unusable=0; bev_ideas={"actions": {"calls": 14, "failed": 0, "rejected": 0, "used": 0}, "clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 40, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 18, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 64, "failed": 0, "rejected": 0, "used": 0}, "verifier": {"calls": 22, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:14:15 | bevideas_shadow | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=39.7 |
| 2026-10-19 14:18:43 | bevideas_shadow | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=259.1; group_top1=0.953; calls=65; unusable=0; bev_ideas={"actions": {"calls": 2, "failed": 0, "rejected": 0, "used": 0}, "clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 58, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 39, "failed": 0, "rejected": 0, "used": 0}, "notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 128, "failed": 0, "rejected": 0, "used": 0}, "verifier": {"calls": 7, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:24:21 | bevideas_shadow | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=39.3 |
| 2026-10-19 14:25:57 | bevideas_shadow | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=88.0; group_top1=1.0; calls=24; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 23, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 2, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 51, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:29:40 | bevideas_shadow | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=39.3 |
| 2026-10-19 14:32:08 | bevideas_shadow | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=140.1; group_top1=0.529; calls=27; unusable=0; bev_ideas={"actions": {"calls": 17, "failed": 0, "rejected": 0, "used": 0}, "clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 27, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 20, "failed": 0, "rejected": 0, "used": 0}, "notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 52, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:37:27 | bevideas_shadow | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=39.7 |
| 2026-10-19 14:41:44 | bevideas_shadow | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=249.6; group_top1=0.429; calls=58; unusable=0; bev_ideas={"actions": {"calls": 34, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 41, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 77, "failed": 0, "rejected": 0, "used": 0}, "verifier": {"calls": 28, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 14:48:21 | bevideas_shadow | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=39.7 |
| 2026-10-19 15:01:02 | bevideas_shadow | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=753.4; group_top1=0.804; calls=134; unusable=0; bev_ideas={"actions": {"calls": 241, "failed": 0, "rejected": 0, "used": 0}, "clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 127, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 8, "failed": 0, "rejected": 0, "used": 0}, "notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 250, "failed": 0, "rejected": 0, "used": 0}, "verifier": {"calls": 9, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 15:07:58 | bevideas_shadow | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=39.7 |
| 2026-10-19 15:13:23 | bevideas_shadow | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=317.2; group_top1=0.939; calls=56; unusable=0; bev_ideas={"actions": {"calls": 132, "failed": 0, "rejected": 0, "used": 0}, "clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 56, "failed": 0, "rejected": 0, "used": 0}, "first": {"calls": 11, "failed": 0, "rejected": 0, "used": 0}, "notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 132, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 15:19:59 | bevideas_shadow | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=39.7 |
| 2026-10-19 15:20:14 | bevideas_shadow | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-19 15:20:45 | bevideas_shadow | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=39.7 |
| 2026-10-19 15:21:03 | bevideas_shadow | episode_done | episode=dev_N02_normal; run=1; wall_s=10.5; calls=1; unusable=0; bev_ideas={"actions": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}, "unknown": {"calls": 1, "failed": 0, "rejected": 0, "used": 0}} |
| 2026-10-19 15:21:04 | bevideas_shadow | batch_end | status=all episodes done |
| 2026-10-19 15:26:24 | bevideas_A1 | batch_start | command=scripts/benchmark.sh bevideas_A1 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-10-19 15:26:44 | bevideas_A1 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=38.6 |
| 2026-10-19 15:28:30 | bevideas_A1 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=98.6; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-19 15:30:18 | bevideas_A1 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=42.0 |
| 2026-10-19 15:32:45 | bevideas_A1 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=138.6; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-19 15:35:49 | bevideas_A1 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=42.0 |
| 2026-10-19 15:39:03 | bevideas_A1 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=186.1; group_top1=0.953; calls=65; unusable=0 |
| 2026-10-19 15:42:28 | bevideas_A1 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=42.0 |
| 2026-10-19 15:43:44 | bevideas_A1 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=68.5; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-19 15:45:51 | bevideas_A1 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=42.0 |
| 2026-10-19 15:47:35 | bevideas_A1 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=96.0; group_top1=0.451; calls=27; unusable=0 |
| 2026-10-19 15:50:02 | bevideas_A1 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=42.0 |
| 2026-10-19 15:53:02 | bevideas_A1 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=171.6; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-19 15:56:07 | bevideas_A1 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=41.8 |
| 2026-10-19 16:03:59 | bevideas_A1 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=464.3; group_top1=0.804; calls=134; unusable=0 |
| 2026-10-19 16:07:42 | bevideas_A1 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=42.0 |
| 2026-10-19 16:10:41 | bevideas_A1 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=171.6; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-19 16:14:05 | bevideas_A1 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=42.0 |
| 2026-10-19 16:14:20 | bevideas_A1 | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 16:14:51 | bevideas_A1 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=41.7 |
| 2026-10-19 16:15:10 | bevideas_A1 | episode_done | episode=dev_N02_normal; run=1; wall_s=10.5; calls=1; unusable=0 |
| 2026-10-19 16:15:11 | bevideas_A1 | batch_end | status=all episodes done |
| 2026-10-19 16:15:11 | bevideas_B_explain | batch_start | command=scripts/benchmark.sh bevideas_B_explain dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on", "bev_device": "npu"} |
| 2026-10-19 16:15:29 | bevideas_B_explain | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=43.4 |
| 2026-10-19 16:16:43 | bevideas_B_explain | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=65.5; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-19 16:17:13 | bevideas_B_explain | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=46.7 |
| 2026-10-19 16:19:05 | bevideas_B_explain | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=103.0; group_top1=0.625; calls=91; unusable=0; bev_ideas={"explain": {"calls": 40, "failed": 0, "rejected": 0, "used": 40}} |
| 2026-10-19 16:20:14 | bevideas_B_explain | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=46.7 |
| 2026-10-19 16:22:29 | bevideas_B_explain | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=128.1; group_top1=0.953; calls=123; unusable=0; bev_ideas={"explain": {"calls": 58, "failed": 0, "rejected": 0, "used": 58}} |
| 2026-10-19 16:23:39 | bevideas_B_explain | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=48.2 |
| 2026-10-19 16:24:30 | bevideas_B_explain | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=43.5; group_top1=1.0; calls=47; unusable=0; bev_ideas={"explain": {"calls": 23, "failed": 0, "rejected": 0, "used": 23}} |
| 2026-10-19 16:25:20 | bevideas_B_explain | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=47.5 |
| 2026-10-19 16:26:32 | bevideas_B_explain | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=64.0; group_top1=0.549; calls=54; unusable=0; bev_ideas={"explain": {"calls": 27, "failed": 0, "rejected": 0, "used": 27}} |
| 2026-10-19 16:27:22 | bevideas_B_explain | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=47.5 |
| 2026-10-19 16:29:21 | bevideas_B_explain | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=111.6; group_top1=0.571; calls=98; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}} |
| 2026-10-19 16:30:52 | bevideas_B_explain | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=46.7 |
| 2026-10-19 16:36:19 | bevideas_B_explain | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=318.7; group_top1=0.804; calls=261; unusable=0; bev_ideas={"explain": {"calls": 127, "failed": 0, "rejected": 0, "used": 127}} |
| 2026-10-19 16:38:06 | bevideas_B_explain | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=47.1 |
| 2026-10-19 16:40:21 | bevideas_B_explain | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=126.6; group_top1=0.939; calls=112; unusable=0; bev_ideas={"explain": {"calls": 56, "failed": 0, "rejected": 0, "used": 56}} |
| 2026-10-19 16:41:50 | bevideas_B_explain | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=46.7 |
| 2026-10-19 16:42:05 | bevideas_B_explain | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 16:42:16 | bevideas_B_explain | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=47.1 |
| 2026-10-19 16:42:34 | bevideas_B_explain | episode_done | episode=dev_N02_normal; run=1; wall_s=9.0; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 16:42:35 | bevideas_B_explain | batch_end | status=all episodes done |
| 2026-10-19 16:42:35 | bevideas_B_actions | batch_start | command=scripts/benchmark.sh bevideas_B_actions dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev actions=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "actions=on", "bev_device": "npu"} |
| 2026-10-19 16:42:53 | bevideas_B_actions | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=47.3 |
| 2026-10-19 16:44:47 | bevideas_B_actions | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=106.2; group_top1=0.561; calls=45; unusable=0; bev_ideas={"actions": {"calls": 14, "failed": 0, "rejected": 0, "used": 14}} |
| 2026-10-19 16:45:18 | bevideas_B_actions | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=51.7 |
| 2026-10-19 16:47:57 | bevideas_B_actions | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=150.6; group_top1=0.625; calls=65; unusable=0; bev_ideas={"actions": {"calls": 14, "failed": 0, "rejected": 0, "used": 14}} |
| 2026-10-19 16:48:47 | bevideas_B_actions | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=51.3 |
| 2026-10-19 16:52:12 | bevideas_B_actions | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=197.1; group_top1=0.953; calls=67; unusable=0; bev_ideas={"actions": {"calls": 2, "failed": 0, "rejected": 0, "used": 2}} |
| 2026-10-19 16:53:21 | bevideas_B_actions | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=50.2 |
| 2026-10-19 16:54:44 | bevideas_B_actions | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=75.0; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-19 16:55:15 | bevideas_B_actions | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=51.7 |
| 2026-10-19 16:57:08 | bevideas_B_actions | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=105.1; group_top1=0.549; calls=44; unusable=0; bev_ideas={"actions": {"calls": 17, "failed": 0, "rejected": 0, "used": 17}} |
| 2026-10-19 16:58:00 | bevideas_B_actions | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=49.8 |
| 2026-10-19 17:01:20 | bevideas_B_actions | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=191.6; group_top1=0.429; calls=92; unusable=0; bev_ideas={"actions": {"calls": 34, "failed": 0, "rejected": 0, "used": 34}} |
| 2026-10-19 17:02:12 | bevideas_B_actions | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=51.3 |
| 2026-10-19 17:12:08 | bevideas_B_actions | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=587.4; group_top1=0.804; calls=375; unusable=0; bev_ideas={"actions": {"calls": 241, "failed": 0, "rejected": 0, "used": 241}} |
| 2026-10-19 17:13:36 | bevideas_B_actions | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=50.2 |
| 2026-10-19 17:17:46 | bevideas_B_actions | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=242.1; group_top1=0.939; calls=188; unusable=0; bev_ideas={"actions": {"calls": 132, "failed": 0, "rejected": 0, "used": 132}} |
| 2026-10-19 17:18:56 | bevideas_B_actions | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=50.9 |
| 2026-10-19 17:19:11 | bevideas_B_actions | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 17:19:22 | bevideas_B_actions | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=50.5 |
| 2026-10-19 17:19:40 | bevideas_B_actions | episode_done | episode=dev_N02_normal; run=1; wall_s=10.0; calls=2; unusable=0; bev_ideas={"actions": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 17:19:41 | bevideas_B_actions | batch_end | status=all episodes done |
| 2026-10-19 17:19:42 | bevideas_B_unknown | batch_start | command=scripts/benchmark.sh bevideas_B_unknown dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev unknown=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "unknown=on", "bev_device": "npu"} |
| 2026-10-19 17:20:18 | bevideas_B_unknown | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=51.3 |
| 2026-10-19 17:22:30 | bevideas_B_unknown | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=124.1; group_top1=0.614; calls=88; unusable=0; bev_ideas={"unknown": {"calls": 57, "failed": 0, "rejected": 0, "used": 57}} |
| 2026-10-19 17:23:01 | bevideas_B_unknown | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=53.6 |
| 2026-10-19 17:25:59 | bevideas_B_unknown | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=169.6; group_top1=0.625; calls=115; unusable=0; bev_ideas={"unknown": {"calls": 64, "failed": 0, "rejected": 0, "used": 64}} |
| 2026-10-19 17:26:31 | bevideas_B_unknown | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=54.4 |
| 2026-10-19 17:30:39 | bevideas_B_unknown | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=239.1; group_top1=0.953; calls=193; unusable=0; bev_ideas={"unknown": {"calls": 128, "failed": 0, "rejected": 0, "used": 128}} |
| 2026-10-19 17:31:31 | bevideas_B_unknown | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=52.9 |
| 2026-10-19 17:33:09 | bevideas_B_unknown | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=90.0; group_top1=1.0; calls=75; unusable=0; bev_ideas={"unknown": {"calls": 51, "failed": 0, "rejected": 0, "used": 51}} |
| 2026-10-19 17:33:42 | bevideas_B_unknown | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=54.0 |
| 2026-10-19 17:35:47 | bevideas_B_unknown | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=117.1; group_top1=0.451; calls=79; unusable=0; bev_ideas={"unknown": {"calls": 52, "failed": 0, "rejected": 0, "used": 52}} |
| 2026-10-19 17:36:20 | bevideas_B_unknown | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=54.8 |
| 2026-10-19 17:39:56 | bevideas_B_unknown | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=208.6; group_top1=0.455; calls=135; unusable=0; bev_ideas={"unknown": {"calls": 77, "failed": 0, "rejected": 0, "used": 77}} |
| 2026-10-19 17:40:48 | bevideas_B_unknown | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=53.2 |
| 2026-10-19 17:50:31 | bevideas_B_unknown | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=574.9; group_top1=0.804; calls=384; unusable=0; bev_ideas={"unknown": {"calls": 250, "failed": 0, "rejected": 0, "used": 250}} |
| 2026-10-19 17:51:23 | bevideas_B_unknown | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=54.4 |
| 2026-10-19 17:55:23 | bevideas_B_unknown | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=231.7; group_top1=0.939; calls=188; unusable=0; bev_ideas={"unknown": {"calls": 132, "failed": 0, "rejected": 0, "used": 132}} |
| 2026-10-19 17:56:15 | bevideas_B_unknown | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=53.2 |
| 2026-10-19 17:56:30 | bevideas_B_unknown | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 17:56:42 | bevideas_B_unknown | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=52.9 |
| 2026-10-19 17:57:00 | bevideas_B_unknown | episode_done | episode=dev_N02_normal; run=1; wall_s=10.5; calls=2; unusable=0; bev_ideas={"unknown": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 17:57:01 | bevideas_B_unknown | batch_end | status=all episodes done |
| 2026-10-19 17:57:02 | bevideas_B_verifier | batch_start | command=scripts/benchmark.sh bevideas_B_verifier dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev verifier=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "verifier=on", "bev_device": "npu"} |
| 2026-10-19 17:57:20 | bevideas_B_verifier | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=52.9 |
| 2026-10-19 17:59:17 | bevideas_B_verifier | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=109.1; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-19 17:59:47 | bevideas_B_verifier | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=54.0 |
| 2026-10-19 18:02:09 | bevideas_B_verifier | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=135.1; group_top1=0.625; calls=73; unusable=0; bev_ideas={"verifier": {"calls": 22, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-10-19 18:02:42 | bevideas_B_verifier | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=55.6 |
| 2026-10-19 18:06:02 | bevideas_B_verifier | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=191.6; group_top1=0.953; calls=72; unusable=0; bev_ideas={"verifier": {"calls": 7, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-19 18:06:35 | bevideas_B_verifier | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=56.7 |
| 2026-10-19 18:07:58 | bevideas_B_verifier | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=75.5; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-19 18:08:31 | bevideas_B_verifier | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=55.6 |
| 2026-10-19 18:10:23 | bevideas_B_verifier | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=103.6; group_top1=0.451; calls=27; unusable=0 |
| 2026-10-19 18:10:55 | bevideas_B_verifier | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=55.2 |
| 2026-10-19 18:13:45 | bevideas_B_verifier | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=161.6; group_top1=0.429; calls=87; unusable=0; bev_ideas={"verifier": {"calls": 29, "failed": 0, "rejected": 0, "used": 16}} |
| 2026-10-19 18:14:18 | bevideas_B_verifier | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=55.6 |
| 2026-10-19 18:22:31 | bevideas_B_verifier | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=484.9; group_top1=0.804; calls=143; unusable=0; bev_ideas={"verifier": {"calls": 9, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-19 18:23:04 | bevideas_B_verifier | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=56.7 |
| 2026-10-19 18:26:23 | bevideas_B_verifier | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=191.6; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-19 18:26:56 | bevideas_B_verifier | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=56.3 |
| 2026-10-19 18:27:11 | bevideas_B_verifier | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-19 18:27:24 | bevideas_B_verifier | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=53.6 |
| 2026-10-19 18:27:42 | bevideas_B_verifier | episode_done | episode=dev_N02_normal; run=1; wall_s=10.0; calls=1; unusable=0 |
| 2026-10-19 18:27:43 | bevideas_B_verifier | batch_end | status=all episodes done |
| 2026-10-19 18:27:44 | bevideas_B_notes | batch_start | command=scripts/benchmark.sh bevideas_B_notes dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev notes=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "notes=on", "bev_device": "npu"} |
| 2026-10-19 18:28:02 | bevideas_B_notes | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=53.1 |
| 2026-10-19 18:29:49 | bevideas_B_notes | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=99.5; group_top1=0.561; calls=32; unusable=0; bev_ideas={"notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 18:30:22 | bevideas_B_notes | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=53.2 |
| 2026-10-19 18:33:01 | bevideas_B_notes | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=151.6; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-19 18:33:34 | bevideas_B_notes | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=54.8 |
| 2026-10-19 18:36:59 | bevideas_B_notes | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=196.6; group_top1=0.953; calls=66; unusable=0; bev_ideas={"notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 18:37:32 | bevideas_B_notes | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=56.0 |
| 2026-10-19 18:38:54 | bevideas_B_notes | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=74.5; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-19 18:39:27 | bevideas_B_notes | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=54.0 |
| 2026-10-19 18:41:14 | bevideas_B_notes | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=99.6; group_top1=0.451; calls=28; unusable=0; bev_ideas={"notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 18:41:47 | bevideas_B_notes | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=54.4 |
| 2026-10-19 18:44:58 | bevideas_B_notes | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=182.6; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-19 18:45:31 | bevideas_B_notes | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=56.7 |
| 2026-10-19 18:53:54 | bevideas_B_notes | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=494.8; group_top1=0.804; calls=135; unusable=0; bev_ideas={"notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 18:54:27 | bevideas_B_notes | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=57.1 |
| 2026-10-19 18:57:45 | bevideas_B_notes | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=190.6; group_top1=0.939; calls=56; unusable=0; bev_ideas={"notes": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-19 18:58:18 | bevideas_B_notes | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=56.7 |
| 2026-10-19 18:58:33 | bevideas_B_notes | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 18:58:46 | bevideas_B_notes | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=54.4 |
| 2026-10-19 18:59:04 | bevideas_B_notes | episode_done | episode=dev_N02_normal; run=1; wall_s=10.0; calls=1; unusable=0 |
| 2026-10-19 18:59:05 | bevideas_B_notes | batch_end | status=all episodes done |
| 2026-10-19 18:59:06 | bevideas_B_skip | batch_start | command=scripts/benchmark.sh bevideas_B_skip dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev clear_skip=on; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "clear_skip=on", "bev_device": "npu"} |
| 2026-10-19 18:59:24 | bevideas_B_skip | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=53.5 |
| 2026-10-19 19:01:22 | bevideas_B_skip | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=110.6; group_top1=0.614; calls=31; unusable=0 |
| 2026-10-19 19:01:55 | bevideas_B_skip | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=54.0 |
| 2026-10-19 19:04:19 | bevideas_B_skip | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=136.1; group_top1=0.625; calls=46; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-19 19:04:52 | bevideas_B_skip | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=55.2 |
| 2026-10-19 19:08:08 | bevideas_B_skip | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=188.1; group_top1=0.953; calls=60; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-10-19 19:08:41 | bevideas_B_skip | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=56.3 |
| 2026-10-19 19:09:49 | bevideas_B_skip | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=60.5; group_top1=1.0; calls=19; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 16}} |
| 2026-10-19 19:10:22 | bevideas_B_skip | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=54.8 |
| 2026-10-19 19:12:06 | bevideas_B_skip | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=95.5; group_top1=0.471; calls=25; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}} |
| 2026-10-19 19:12:39 | bevideas_B_skip | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=54.4 |
| 2026-10-19 19:15:51 | bevideas_B_skip | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=184.6; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-19 19:16:24 | bevideas_B_skip | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=56.3 |
| 2026-10-19 19:22:35 | bevideas_B_skip | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=362.8; group_top1=0.804; calls=99; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 52}} |
| 2026-10-19 19:23:08 | bevideas_B_skip | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=56.7 |
| 2026-10-19 19:25:51 | bevideas_B_skip | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=156.1; group_top1=0.939; calls=45; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 30}} |
| 2026-10-19 19:26:24 | bevideas_B_skip | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=56.7 |
| 2026-10-19 19:26:39 | bevideas_B_skip | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-19 19:26:52 | bevideas_B_skip | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=54.3 |
| 2026-10-19 19:27:10 | bevideas_B_skip | episode_done | episode=dev_N02_normal; run=1; wall_s=10.0; calls=1; unusable=0 |
| 2026-10-19 19:27:11 | bevideas_B_skip | batch_end | status=all episodes done |
| 2026-10-19 19:27:12 | bevideas_A2 | batch_start | command=scripts/benchmark.sh bevideas_A2 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml; git={"commit": "41e2bd0", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-10-19 19:27:29 | bevideas_A2 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=53.6 |
| 2026-10-19 19:29:24 | bevideas_A2 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=106.6; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-19 19:29:54 | bevideas_A2 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=55.2 |
| 2026-10-19 19:32:35 | bevideas_A2 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=152.6; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-19 19:33:07 | bevideas_A2 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=57.4 |
| 2026-10-19 19:36:40 | bevideas_A2 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=205.6; group_top1=0.953; calls=65; unusable=0 |
| 2026-10-19 19:37:13 | bevideas_A2 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=57.5 |
| 2026-10-19 19:38:38 | bevideas_A2 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=77.0; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-19 19:39:11 | bevideas_A2 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=56.0 |
| 2026-10-19 19:41:05 | bevideas_A2 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=105.5; group_top1=0.51; calls=27; unusable=0 |
| 2026-10-19 19:41:38 | bevideas_A2 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=56.7 |
| 2026-10-19 19:44:54 | bevideas_A2 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=189.1; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-19 19:45:27 | bevideas_A2 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=57.9 |
| 2026-10-19 19:54:09 | bevideas_A2 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=513.3; group_top1=0.804; calls=134; unusable=0 |
| 2026-10-19 19:55:01 | bevideas_A2 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=56.3 |
| 2026-10-19 19:58:25 | bevideas_A2 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=196.1; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-19 19:58:58 | bevideas_A2 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=58.3 |
| 2026-10-19 19:59:13 | bevideas_A2 | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-19 19:59:27 | bevideas_A2 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=56.0 |
| 2026-10-19 19:59:44 | bevideas_A2 | episode_done | episode=dev_N02_normal; run=1; wall_s=10.0; calls=1; unusable=0 |
| 2026-10-19 19:59:46 | bevideas_A2 | batch_end | status=all episodes done |
| 2026-10-21 00:23:05 | bevideas_C_combo_r1 | batch_start | command=scripts/benchmark.sh bevideas_C_combo_r1 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on,clear_skip=on,verifier=on --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on,clear_skip=on,verifier=on", "bev_device": "npu"} |
| 2026-10-21 00:23:23 | bevideas_C_combo_r1 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=46.1 |
| 2026-10-21 00:24:35 | bevideas_C_combo_r1 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=63.5; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-21 00:25:06 | bevideas_C_combo_r1 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=48.6 |
| 2026-10-21 00:26:36 | bevideas_C_combo_r1 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=81.5; group_top1=0.625; calls=105; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 36, "failed": 0, "rejected": 0, "used": 36}, "verifier": {"calls": 22, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-10-21 00:27:06 | bevideas_C_combo_r1 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=49.0 |
| 2026-10-21 00:29:00 | bevideas_C_combo_r1 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=105.5; group_top1=0.953; calls=120; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 11}, "explain": {"calls": 53, "failed": 0, "rejected": 0, "used": 53}, "verifier": {"calls": 7, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 00:29:50 | bevideas_C_combo_r1 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=47.8 |
| 2026-10-21 00:30:33 | bevideas_C_combo_r1 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=35.5; group_top1=1.0; calls=39; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 15}, "explain": {"calls": 19, "failed": 0, "rejected": 0, "used": 19}} |
| 2026-10-21 00:31:04 | bevideas_C_combo_r1 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=48.2 |
| 2026-10-21 00:32:09 | bevideas_C_combo_r1 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=57.5; group_top1=0.549; calls=50; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}, "explain": {"calls": 25, "failed": 0, "rejected": 0, "used": 25}} |
| 2026-10-21 00:32:40 | bevideas_C_combo_r1 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=49.0 |
| 2026-10-21 00:34:19 | bevideas_C_combo_r1 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=90.5; group_top1=0.597; calls=117; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}, "verifier": {"calls": 21, "failed": 0, "rejected": 0, "used": 12}} |
| 2026-10-21 00:35:09 | bevideas_C_combo_r1 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=49.0 |
| 2026-10-21 00:39:31 | bevideas_C_combo_r1 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=253.6; group_top1=0.804; calls=227; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 36}, "explain": {"calls": 105, "failed": 0, "rejected": 0, "used": 105}, "verifier": {"calls": 9, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 00:40:40 | bevideas_C_combo_r1 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=50.5 |
| 2026-10-21 00:42:31 | bevideas_C_combo_r1 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=102.6; group_top1=0.939; calls=90; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 31}, "explain": {"calls": 45, "failed": 0, "rejected": 0, "used": 45}} |
| 2026-10-21 00:43:40 | bevideas_C_combo_r1 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=50.5 |
| 2026-10-21 00:43:55 | bevideas_C_combo_r1 | episode_done | episode=dev_N01_normal; run=1; wall_s=7.0; calls=0; unusable=0 |
| 2026-10-21 00:44:07 | bevideas_C_combo_r1 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=50.5 |
| 2026-10-21 00:44:24 | bevideas_C_combo_r1 | episode_done | episode=dev_N02_normal; run=1; wall_s=8.5; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-21 00:44:25 | bevideas_C_combo_r1 | batch_end | status=all episodes done |
| 2026-10-21 00:54:46 | bevideas_B_explain_bevcpu | batch_start | command=scripts/benchmark.sh bevideas_B_explain_bevcpu dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on --bev-device cpu --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on", "bev_device": "cpu"} |
| 2026-10-21 00:55:11 | bevideas_B_explain_bevcpu | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=38.2 |
| 2026-10-21 00:56:48 | bevideas_B_explain_bevcpu | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=90.0; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-21 00:58:56 | bevideas_B_explain_bevcpu | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=41.1 |
| 2026-10-21 01:01:49 | bevideas_B_explain_bevcpu | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=165.1; group_top1=0.625; calls=91; unusable=0; bev_ideas={"explain": {"calls": 40, "failed": 0, "rejected": 0, "used": 40}} |
| 2026-10-21 01:06:13 | bevideas_B_explain_bevcpu | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=41.3 |
| 2026-10-21 01:09:12 | bevideas_B_explain_bevcpu | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=171.6; group_top1=0.945; calls=124; unusable=0; bev_ideas={"explain": {"calls": 58, "failed": 0, "rejected": 0, "used": 58}} |
| 2026-10-21 01:13:16 | bevideas_B_explain_bevcpu | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=41.1 |
| 2026-10-21 01:14:13 | bevideas_B_explain_bevcpu | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=48.5; group_top1=1.0; calls=47; unusable=0; bev_ideas={"explain": {"calls": 23, "failed": 0, "rejected": 0, "used": 23}} |
| 2026-10-21 01:16:21 | bevideas_B_explain_bevcpu | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=40.9 |
| 2026-10-21 01:18:03 | bevideas_B_explain_bevcpu | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=94.0; group_top1=0.569; calls=54; unusable=0; bev_ideas={"explain": {"calls": 27, "failed": 0, "rejected": 0, "used": 27}} |
| 2026-10-21 01:21:28 | bevideas_B_explain_bevcpu | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=41.1 |
| 2026-10-21 01:24:00 | bevideas_B_explain_bevcpu | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=143.6; group_top1=0.597; calls=96; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}} |
| 2026-10-21 01:28:24 | bevideas_B_explain_bevcpu | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=41.1 |
| 2026-10-21 01:38:33 | bevideas_B_explain_bevcpu | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=601.2; group_top1=0.804; calls=261; unusable=0; bev_ideas={"explain": {"calls": 127, "failed": 0, "rejected": 0, "used": 127}} |
| 2026-10-21 01:44:52 | bevideas_B_explain_bevcpu | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=40.7 |
| 2026-10-21 01:49:00 | bevideas_B_explain_bevcpu | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=239.1; group_top1=0.939; calls=112; unusable=0; bev_ideas={"explain": {"calls": 56, "failed": 0, "rejected": 0, "used": 56}} |
| 2026-10-21 01:54:21 | bevideas_B_explain_bevcpu | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=41.3 |
| 2026-10-21 01:54:36 | bevideas_B_explain_bevcpu | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 01:55:07 | bevideas_B_explain_bevcpu | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=40.3 |
| 2026-10-21 01:55:23 | bevideas_B_explain_bevcpu | episode_done | episode=dev_N02_normal; run=1; wall_s=8.5; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-21 01:55:26 | bevideas_B_explain_bevcpu | batch_end | status=all episodes done |
| 2026-10-21 02:05:39 | bevideas_C_combo_r2 | batch_start | command=scripts/benchmark.sh bevideas_C_combo_r2 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on,clear_skip=on,verifier=on --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on,clear_skip=on,verifier=on", "bev_device": "npu"} |
| 2026-10-21 02:05:56 | bevideas_C_combo_r2 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=36.8 |
| 2026-10-21 02:07:08 | bevideas_C_combo_r2 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=64.0; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-21 02:08:18 | bevideas_C_combo_r2 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=40.5 |
| 2026-10-21 02:09:48 | bevideas_C_combo_r2 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=81.5; group_top1=0.625; calls=105; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 36, "failed": 0, "rejected": 0, "used": 36}, "verifier": {"calls": 22, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-10-21 02:12:14 | bevideas_C_combo_r2 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=41.3 |
| 2026-10-21 02:14:06 | bevideas_C_combo_r2 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=103.5; group_top1=0.953; calls=120; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 53, "failed": 0, "rejected": 0, "used": 53}, "verifier": {"calls": 7, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 02:18:08 | bevideas_C_combo_r2 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=41.3 |
| 2026-10-21 02:18:51 | bevideas_C_combo_r2 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=35.0; group_top1=1.0; calls=39; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 15}, "explain": {"calls": 19, "failed": 0, "rejected": 0, "used": 19}} |
| 2026-10-21 02:20:58 | bevideas_C_combo_r2 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=41.3 |
| 2026-10-21 02:22:03 | bevideas_C_combo_r2 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=56.5; group_top1=0.549; calls=50; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}, "explain": {"calls": 25, "failed": 0, "rejected": 0, "used": 25}} |
| 2026-10-21 02:24:49 | bevideas_C_combo_r2 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=40.9 |
| 2026-10-21 02:26:25 | bevideas_C_combo_r2 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=88.5; group_top1=0.597; calls=117; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}, "verifier": {"calls": 21, "failed": 0, "rejected": 0, "used": 12}} |
| 2026-10-21 02:29:49 | bevideas_C_combo_r2 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=41.3 |
| 2026-10-21 02:34:07 | bevideas_C_combo_r2 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=249.6; group_top1=0.804; calls=228; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 36}, "explain": {"calls": 106, "failed": 0, "rejected": 0, "used": 106}, "verifier": {"calls": 9, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 02:39:45 | bevideas_C_combo_r2 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=41.3 |
| 2026-10-21 02:41:31 | bevideas_C_combo_r2 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=98.0; group_top1=0.939; calls=90; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 31}, "explain": {"calls": 45, "failed": 0, "rejected": 0, "used": 45}} |
| 2026-10-21 02:45:34 | bevideas_C_combo_r2 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=41.3 |
| 2026-10-21 02:45:49 | bevideas_C_combo_r2 | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 02:46:19 | bevideas_C_combo_r2 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=41.3 |
| 2026-10-21 02:46:36 | bevideas_C_combo_r2 | episode_done | episode=dev_N02_normal; run=1; wall_s=8.0; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-21 02:46:37 | bevideas_C_combo_r2 | batch_end | status=all episodes done |
| 2026-10-21 02:56:46 | bevideas_C_combo_r3 | batch_start | command=scripts/benchmark.sh bevideas_C_combo_r3 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on,clear_skip=on,verifier=on --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on,clear_skip=on,verifier=on", "bev_device": "npu"} |
| 2026-10-21 02:57:04 | bevideas_C_combo_r3 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=37.6 |
| 2026-10-21 02:58:15 | bevideas_C_combo_r3 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=63.0; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-21 02:59:24 | bevideas_C_combo_r3 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=41.7 |
| 2026-10-21 03:00:53 | bevideas_C_combo_r3 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=81.5; group_top1=0.625; calls=105; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 36, "failed": 0, "rejected": 0, "used": 36}, "verifier": {"calls": 22, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-10-21 03:03:00 | bevideas_C_combo_r3 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=42.4 |
| 2026-10-21 03:04:53 | bevideas_C_combo_r3 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=104.5; group_top1=0.953; calls=120; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 53, "failed": 0, "rejected": 0, "used": 53}, "verifier": {"calls": 7, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 03:07:58 | bevideas_C_combo_r3 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=42.4 |
| 2026-10-21 03:08:41 | bevideas_C_combo_r3 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=35.0; group_top1=1.0; calls=39; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 15}, "explain": {"calls": 19, "failed": 0, "rejected": 0, "used": 19}} |
| 2026-10-21 03:10:48 | bevideas_C_combo_r3 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=42.4 |
| 2026-10-21 03:11:52 | bevideas_C_combo_r3 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=56.5; group_top1=0.549; calls=50; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}, "explain": {"calls": 25, "failed": 0, "rejected": 0, "used": 25}} |
| 2026-10-21 03:13:59 | bevideas_C_combo_r3 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=42.0 |
| 2026-10-21 03:15:35 | bevideas_C_combo_r3 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=88.5; group_top1=0.597; calls=117; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}, "verifier": {"calls": 21, "failed": 0, "rejected": 0, "used": 12}} |
| 2026-10-21 03:18:20 | bevideas_C_combo_r3 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=42.0 |
| 2026-10-21 03:22:34 | bevideas_C_combo_r3 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=245.1; group_top1=0.804; calls=223; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 36}, "explain": {"calls": 103, "failed": 0, "rejected": 0, "used": 103}, "verifier": {"calls": 9, "failed": 0, "rejected": 0, "used": 7}} |
| 2026-10-21 03:27:15 | bevideas_C_combo_r3 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=42.4 |
| 2026-10-21 03:29:01 | bevideas_C_combo_r3 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=98.5; group_top1=0.939; calls=90; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 31}, "explain": {"calls": 45, "failed": 0, "rejected": 0, "used": 45}} |
| 2026-10-21 03:32:08 | bevideas_C_combo_r3 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=42.4 |
| 2026-10-21 03:32:23 | bevideas_C_combo_r3 | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 03:32:56 | bevideas_C_combo_r3 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=42.0 |
| 2026-10-21 03:33:12 | bevideas_C_combo_r3 | episode_done | episode=dev_N02_normal; run=1; wall_s=8.5; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-21 03:33:14 | bevideas_C_combo_r3 | batch_end | status=all episodes done |
| 2026-10-21 03:43:22 | bevideas_A3 | batch_start | command=scripts/benchmark.sh bevideas_A3 dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-10-21 03:43:42 | bevideas_A3 | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=37.4 |
| 2026-10-21 03:45:29 | bevideas_A3 | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=98.5; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-21 03:47:55 | bevideas_A3 | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=42.0 |
| 2026-10-21 03:50:23 | bevideas_A3 | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=140.1; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-21 03:54:26 | bevideas_A3 | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=41.7 |
| 2026-10-21 03:57:41 | bevideas_A3 | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=187.1; group_top1=0.953; calls=65; unusable=0 |
| 2026-10-21 04:02:41 | bevideas_A3 | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=41.8 |
| 2026-10-21 04:03:58 | bevideas_A3 | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=68.5; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-21 04:06:44 | bevideas_A3 | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=42.0 |
| 2026-10-21 04:08:25 | bevideas_A3 | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=93.5; group_top1=0.471; calls=27; unusable=0 |
| 2026-10-21 04:11:49 | bevideas_A3 | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=42.0 |
| 2026-10-21 04:14:52 | bevideas_A3 | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=174.1; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-21 04:19:52 | bevideas_A3 | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=41.7 |
| 2026-10-21 04:28:01 | bevideas_A3 | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=480.2; group_top1=0.804; calls=134; unusable=0 |
| 2026-10-21 04:33:59 | bevideas_A3 | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=42.0 |
| 2026-10-21 04:37:04 | bevideas_A3 | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=177.1; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-21 04:42:24 | bevideas_A3 | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=41.7 |
| 2026-10-21 04:42:38 | bevideas_A3 | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 04:43:09 | bevideas_A3 | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=42.0 |
| 2026-10-21 04:43:26 | bevideas_A3 | episode_done | episode=dev_N02_normal; run=1; wall_s=9.5; calls=1; unusable=0 |
| 2026-10-21 04:43:27 | bevideas_A3 | batch_end | status=all episodes done |
| 2026-10-21 04:53:36 | bevideas_A_soak | batch_start | command=scripts/benchmark.sh bevideas_A_soak dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --cool-max 0 --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-10-21 04:53:54 | bevideas_A_soak | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=37.8 |
| 2026-10-21 04:55:40 | bevideas_A_soak | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=98.0; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-21 04:55:52 | bevideas_A_soak | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=54.0 |
| 2026-10-21 04:58:24 | bevideas_A_soak | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=144.1; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-21 04:58:35 | bevideas_A_soak | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=59.8 |
| 2026-10-21 05:02:05 | bevideas_A_soak | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=202.1; group_top1=0.953; calls=65; unusable=0 |
| 2026-10-21 05:02:19 | bevideas_A_soak | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=63.3 |
| 2026-10-21 05:03:46 | bevideas_A_soak | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=79.0; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-21 05:04:00 | bevideas_A_soak | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=62.9 |
| 2026-10-21 05:05:55 | bevideas_A_soak | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=106.5; group_top1=0.451; calls=27; unusable=0 |
| 2026-10-21 05:06:08 | bevideas_A_soak | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=63.3 |
| 2026-10-21 05:09:31 | bevideas_A_soak | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=195.1; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-21 05:09:43 | bevideas_A_soak | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=64.8 |
| 2026-10-21 05:18:33 | bevideas_A_soak | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=522.2; group_top1=0.804; calls=134; unusable=0 |
| 2026-10-21 05:18:47 | bevideas_A_soak | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=64.8 |
| 2026-10-21 05:22:17 | bevideas_A_soak | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=202.1; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-21 05:22:30 | bevideas_A_soak | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=64.8 |
| 2026-10-21 05:22:45 | bevideas_A_soak | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 05:22:59 | bevideas_A_soak | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=59.8 |
| 2026-10-21 05:23:15 | bevideas_A_soak | episode_done | episode=dev_N02_normal; run=1; wall_s=9.5; calls=1; unusable=0 |
| 2026-10-21 05:23:16 | bevideas_A_soak | batch_end | status=all episodes done |
| 2026-10-21 05:50:44 | bevideas_A_meas | batch_start | command=scripts/benchmark.sh bevideas_A_meas dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-10-21 05:51:01 | bevideas_A_meas | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=36.8 |
| 2026-10-21 05:52:47 | bevideas_A_meas | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=98.0; group_top1=0.561; calls=31; unusable=0 |
| 2026-10-21 05:55:13 | bevideas_A_meas | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=40.5 |
| 2026-10-21 05:57:40 | bevideas_A_meas | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=139.6; group_top1=0.625; calls=51; unusable=0 |
| 2026-10-21 06:03:02 | bevideas_A_meas | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=40.9 |
| 2026-10-21 06:06:15 | bevideas_A_meas | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=185.6; group_top1=0.953; calls=65; unusable=0 |
| 2026-10-21 06:11:55 | bevideas_A_meas | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=40.1 |
| 2026-10-21 06:13:13 | bevideas_A_meas | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=69.0; group_top1=1.0; calls=24; unusable=0 |
| 2026-10-21 06:16:37 | bevideas_A_meas | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=40.9 |
| 2026-10-21 06:18:20 | bevideas_A_meas | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=95.5; group_top1=0.471; calls=27; unusable=0 |
| 2026-10-21 06:22:02 | bevideas_A_meas | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=40.9 |
| 2026-10-21 06:25:02 | bevideas_A_meas | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=171.6; group_top1=0.429; calls=58; unusable=0 |
| 2026-10-21 06:30:02 | bevideas_A_meas | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=40.9 |
| 2026-10-21 06:38:03 | bevideas_A_meas | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=472.2; group_top1=0.804; calls=134; unusable=0 |
| 2026-10-21 06:44:20 | bevideas_A_meas | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=40.9 |
| 2026-10-21 06:47:21 | bevideas_A_meas | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=173.1; group_top1=0.939; calls=56; unusable=0 |
| 2026-10-21 06:52:21 | bevideas_A_meas | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=40.5 |
| 2026-10-21 06:52:36 | bevideas_A_meas | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 06:53:25 | bevideas_A_meas | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=40.9 |
| 2026-10-21 06:53:42 | bevideas_A_meas | episode_done | episode=dev_N02_normal; run=1; wall_s=9.5; calls=1; unusable=0 |
| 2026-10-21 06:53:43 | bevideas_A_meas | batch_end | status=all episodes done |
| 2026-10-21 07:03:52 | bevideas_B_explain_meas | batch_start | command=scripts/benchmark.sh bevideas_B_explain_meas dev_A01_fcv_seize dev_A02_fcv_seize_fast dev_B01_tube_leak dev_B02_tube_leak_fast dev_C01_wet_coal dev_C02_feeder_trip dev_D01_high_cv_coal dev_D03_high_cv_severe dev_N01_normal dev_N02_normal --overlay configs/bev_ideas.yaml --bev explain=on --plain; git={"commit": "4c527f8", "branch": "bev-ideas", "uncommitted_changes": false}; episodes=10; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml", "overlay_sha256": "194387069d0771ef", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on", "bev_device": "npu"} |
| 2026-10-21 07:04:10 | bevideas_B_explain_meas | episode_start | episode=dev_A01_fcv_seize; run=1; stem=dev_A01_fcv_seize_multi; chip_c=36.8 |
| 2026-10-21 07:05:21 | bevideas_B_explain_meas | episode_done | episode=dev_A01_fcv_seize; run=1; wall_s=63.0; group_top1=0.509; calls=62; unusable=0; bev_ideas={"explain": {"calls": 31, "failed": 0, "rejected": 0, "used": 31}} |
| 2026-10-21 07:06:30 | bevideas_B_explain_meas | episode_start | episode=dev_A02_fcv_seize_fast; run=1; stem=dev_A02_fcv_seize_fast_multi; chip_c=40.9 |
| 2026-10-21 07:08:18 | bevideas_B_explain_meas | episode_done | episode=dev_A02_fcv_seize_fast; run=1; wall_s=100.0; group_top1=0.625; calls=91; unusable=0; bev_ideas={"explain": {"calls": 40, "failed": 0, "rejected": 0, "used": 40}} |
| 2026-10-21 07:12:21 | bevideas_B_explain_meas | episode_start | episode=dev_B01_tube_leak; run=1; stem=dev_B01_tube_leak_multi; chip_c=40.5 |
| 2026-10-21 07:14:34 | bevideas_B_explain_meas | episode_done | episode=dev_B01_tube_leak; run=1; wall_s=124.6; group_top1=0.945; calls=124; unusable=0; bev_ideas={"explain": {"calls": 58, "failed": 0, "rejected": 0, "used": 58}} |
| 2026-10-21 07:18:55 | bevideas_B_explain_meas | episode_start | episode=dev_B02_tube_leak_fast; run=1; stem=dev_B02_tube_leak_fast_multi; chip_c=40.9 |
| 2026-10-21 07:19:43 | bevideas_B_explain_meas | episode_done | episode=dev_B02_tube_leak_fast; run=1; wall_s=40.5; group_top1=1.0; calls=47; unusable=0; bev_ideas={"explain": {"calls": 23, "failed": 0, "rejected": 0, "used": 23}} |
| 2026-10-21 07:22:11 | bevideas_B_explain_meas | episode_start | episode=dev_C01_wet_coal; run=1; stem=dev_C01_wet_coal_multi; chip_c=40.9 |
| 2026-10-21 07:23:19 | bevideas_B_explain_meas | episode_done | episode=dev_C01_wet_coal; run=1; wall_s=60.0; group_top1=0.549; calls=54; unusable=0; bev_ideas={"explain": {"calls": 27, "failed": 0, "rejected": 0, "used": 27}} |
| 2026-10-21 07:26:43 | bevideas_B_explain_meas | episode_start | episode=dev_C02_feeder_trip; run=1; stem=dev_C02_feeder_trip_multi; chip_c=40.1 |
| 2026-10-21 07:28:34 | bevideas_B_explain_meas | episode_done | episode=dev_C02_feeder_trip; run=1; wall_s=102.5; group_top1=0.597; calls=96; unusable=0; bev_ideas={"explain": {"calls": 42, "failed": 0, "rejected": 0, "used": 42}} |
| 2026-10-21 07:32:36 | bevideas_B_explain_meas | episode_start | episode=dev_D01_high_cv_coal; run=1; stem=dev_D01_high_cv_coal_multi; chip_c=40.9 |
| 2026-10-21 07:37:52 | bevideas_B_explain_meas | episode_done | episode=dev_D01_high_cv_coal; run=1; wall_s=307.1; group_top1=0.804; calls=261; unusable=0; bev_ideas={"explain": {"calls": 127, "failed": 0, "rejected": 0, "used": 127}} |
| 2026-10-21 07:43:50 | bevideas_B_explain_meas | episode_start | episode=dev_D03_high_cv_severe; run=1; stem=dev_D03_high_cv_severe_multi; chip_c=40.9 |
| 2026-10-21 07:46:00 | bevideas_B_explain_meas | episode_done | episode=dev_D03_high_cv_severe; run=1; wall_s=122.1; group_top1=0.939; calls=112; unusable=0; bev_ideas={"explain": {"calls": 56, "failed": 0, "rejected": 0, "used": 56}} |
| 2026-10-21 07:50:02 | bevideas_B_explain_meas | episode_start | episode=dev_N01_normal; run=1; stem=dev_N01_normal_multi; chip_c=40.9 |
| 2026-10-21 07:50:17 | bevideas_B_explain_meas | episode_done | episode=dev_N01_normal; run=1; wall_s=6.5; calls=0; unusable=0 |
| 2026-10-21 07:50:48 | bevideas_B_explain_meas | episode_start | episode=dev_N02_normal; run=1; stem=dev_N02_normal_multi; chip_c=40.9 |
| 2026-10-21 07:51:04 | bevideas_B_explain_meas | episode_done | episode=dev_N02_normal; run=1; wall_s=8.0; calls=2; unusable=0; bev_ideas={"explain": {"calls": 1, "failed": 0, "rejected": 0, "used": 1}} |
| 2026-10-21 07:51:05 | bevideas_B_explain_meas | batch_end | status=all episodes done |
| 2026-11-06 02:53:46 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/v3.yaml,configs/tep.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 02:54:03 | tep_v3_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=31.6 |
| 2026-11-06 03:16:14 | tep_v3_board | episode_done | episode=tep_board_F01_r1; run=1; wall_s=1321.7; group_top1=0.295; calls=363; unusable=0 |
| 2026-11-06 03:22:15 | tep_v3_board | episode_start | episode=tep_board_F02_r1; run=1; stem=tep_board_F02_r1_multi; chip_c=37.2 |
| 2026-11-06 03:40:36 | tep_v3_board | episode_done | episode=tep_board_F02_r1; run=1; wall_s=1093.1; group_top1=0.623; calls=335; unusable=0 |
| 2026-11-06 03:46:18 | tep_v3_board | episode_start | episode=tep_board_F03_r1; run=1; stem=tep_board_F03_r1_multi; chip_c=37.2 |
| 2026-11-06 03:50:16 | tep_v3_board | episode_done | episode=tep_board_F03_r1; run=1; wall_s=229.2; group_top1=0.0; calls=117; unusable=0 |
| 2026-11-06 03:55:37 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=36.8 |
| 2026-11-06 04:03:08 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:03:08 | tep_v3_board | board_lost | episode=tep_board_F04_r1 |
| 2026-11-06 04:03:18 | tep_v3_board | board_back | episode=tep_board_F04_r1; waited_s=10 |
| 2026-11-06 04:14:06 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=37.0 |
| 2026-11-06 04:14:14 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:14:14 | tep_v3_board | board_lost | episode=tep_board_F04_r1 |
| 2026-11-06 04:14:29 | tep_v3_board | board_back | episode=tep_board_F04_r1; waited_s=15 |
| 2026-11-06 04:24:55 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=37.4 |
| 2026-11-06 04:25:04 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:25:04 | tep_v3_board | board_lost | episode=tep_board_F04_r1 |
| 2026-11-06 04:25:09 | tep_v3_board | board_back | episode=tep_board_F04_r1; waited_s=5 |
| 2026-11-06 04:32:35 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F04_r1 --overlay configs/v3.yaml,configs/tep.yaml --plain --cool-max 20 --max-reconnects 0; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=1; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 04:32:49 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=45.1 |
| 2026-11-06 04:32:59 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:32:59 | tep_v3_board | batch_end | status=error; error=tep_board_F04_r1: the board connection dropped 1 times; stopping. Run the same command again to continue from tep_board_F04_r1. |
| 2026-11-06 04:48:05 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/v3.yaml,configs/tep.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 04:48:11 | tep_v3_board | skip | episode=tep_board_F01_r1; why=already has run 1 |
| 2026-11-06 04:48:11 | tep_v3_board | skip | episode=tep_board_F02_r1; why=already has run 1 |
| 2026-11-06 04:48:11 | tep_v3_board | skip | episode=tep_board_F03_r1; why=already has run 1 |
| 2026-11-06 04:48:23 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=37.4 |
| 2026-11-06 04:48:36 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:48:36 | tep_v3_board | board_lost | episode=tep_board_F04_r1 |
| 2026-11-06 04:49:42 | tep_v3_board | board_back | episode=tep_board_F04_r1; waited_s=65 |
| 2026-11-06 04:49:58 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=38.6 |
| 2026-11-06 04:50:10 | tep_v3_board | episode_failed | episode=tep_board_F04_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 04:50:10 | tep_v3_board | board_lost | episode=tep_board_F04_r1 |
| 2026-11-06 04:50:40 | tep_v3_board | board_back | episode=tep_board_F04_r1; waited_s=30 |
| 2026-11-06 04:50:55 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=39.0 |
| 2026-11-06 04:52:05 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/v3.yaml,configs/tep.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 04:52:10 | tep_v3_board | skip | episode=tep_board_F01_r1; why=already has run 1 |
| 2026-11-06 04:52:10 | tep_v3_board | skip | episode=tep_board_F02_r1; why=already has run 1 |
| 2026-11-06 04:52:10 | tep_v3_board | skip | episode=tep_board_F03_r1; why=already has run 1 |
| 2026-11-06 04:52:22 | tep_v3_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=41.8 |
| 2026-11-06 04:52:45 | tep_v3_board | episode_done | episode=tep_board_F04_r1; run=1; wall_s=13.6; group_top1=0.805; calls=221; unusable=2 |
| 2026-11-06 04:52:58 | tep_v3_board | episode_start | episode=tep_board_F05_r1; run=1; stem=tep_board_F05_r1_multi; chip_c=40.1 |
| 2026-11-06 05:14:58 | tep_v3_board | episode_done | episode=tep_board_F05_r1; run=1; wall_s=1310.4; group_top1=0.0; calls=368; unusable=0 |
| 2026-11-06 05:16:27 | tep_v3_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=48.0 |
| 2026-11-06 05:20:09 | tep_v3_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 05:20:09 | tep_v3_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 05:21:00 | tep_v3_board | board_back | episode=tep_board_F06_r1; waited_s=50 |
| 2026-11-06 05:22:47 | tep_v3_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=47.7 |
| 2026-11-06 05:22:55 | tep_v3_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 05:22:55 | tep_v3_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 05:23:10 | tep_v3_board | board_back | episode=tep_board_F06_r1; waited_s=15 |
| 2026-11-06 05:23:25 | tep_v3_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=46.1 |
| 2026-11-06 05:32:44 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/v3.yaml,configs/tep.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 05:32:50 | tep_v3_board | skip | episode=tep_board_F01_r1; why=already has run 1 |
| 2026-11-06 05:32:50 | tep_v3_board | skip | episode=tep_board_F02_r1; why=already has run 1 |
| 2026-11-06 05:32:50 | tep_v3_board | skip | episode=tep_board_F03_r1; why=already has run 1 |
| 2026-11-06 05:32:50 | tep_v3_board | skip | episode=tep_board_F04_r1; why=already has run 1 |
| 2026-11-06 05:32:50 | tep_v3_board | skip | episode=tep_board_F05_r1; why=already has run 1 |
| 2026-11-06 05:33:02 | tep_v3_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=51.9 |
| 2026-11-06 05:42:16 | tep_v3_board | episode_done | episode=tep_board_F06_r1; run=1; wall_s=544.3; group_top1=0.824; calls=351; unusable=1 |
| 2026-11-06 05:42:48 | tep_v3_board | episode_start | episode=tep_board_F07_r1; run=1; stem=tep_board_F07_r1_multi; chip_c=54.4 |
| 2026-11-06 06:08:45 | tep_v3_board | episode_done | episode=tep_board_F07_r1; run=1; wall_s=1546.7; group_top1=0.006; calls=379; unusable=0 |
| 2026-11-06 06:09:17 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=55.2 |
| 2026-11-06 06:16:11 | tep_v3_board | episode_failed | episode=tep_board_F08_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 06:16:11 | tep_v3_board | board_lost | episode=tep_board_F08_r1 |
| 2026-11-06 06:16:36 | tep_v3_board | board_back | episode=tep_board_F08_r1; waited_s=25 |
| 2026-11-06 06:17:10 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=55.2 |
| 2026-11-06 06:17:18 | tep_v3_board | episode_failed | episode=tep_board_F08_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 06:17:18 | tep_v3_board | board_lost | episode=tep_board_F08_r1 |
| 2026-11-06 06:18:24 | tep_v3_board | board_back | episode=tep_board_F08_r1; waited_s=65 |
| 2026-11-06 06:18:39 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=52.1 |
| 2026-11-06 06:19:46 | tep_v3_board | batch_start | command=scripts/benchmark.sh tep_v3_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/v3.yaml,configs/tep.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "1f7b422", "branch": "breadth-tep", "uncommitted_changes": true}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/tep.yaml", "overlay_sha256": "22a954137f5b0df0", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F01_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F02_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F03_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F04_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F05_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F06_r1; why=already has run 1 |
| 2026-11-06 06:19:52 | tep_v3_board | skip | episode=tep_board_F07_r1; why=already has run 1 |
| 2026-11-06 06:20:04 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=45.1 |
| 2026-11-06 06:20:15 | tep_v3_board | episode_failed | episode=tep_board_F08_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 06:20:15 | tep_v3_board | board_lost | episode=tep_board_F08_r1 |
| 2026-11-06 06:20:40 | tep_v3_board | board_back | episode=tep_board_F08_r1; waited_s=25 |
| 2026-11-06 06:20:56 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=45.1 |
| 2026-11-06 06:29:55 | tep_v3_board | episode_failed | episode=tep_board_F08_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 06:29:55 | tep_v3_board | board_lost | episode=tep_board_F08_r1 |
| 2026-11-06 06:30:45 | tep_v3_board | board_back | episode=tep_board_F08_r1; waited_s=50 |
| 2026-11-06 06:32:12 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=50.9 |
| 2026-11-06 06:32:23 | tep_v3_board | episode_failed | episode=tep_board_F08_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 06:32:23 | tep_v3_board | board_lost | episode=tep_board_F08_r1 |
| 2026-11-06 06:32:48 | tep_v3_board | board_back | episode=tep_board_F08_r1; waited_s=25 |
| 2026-11-06 06:33:03 | tep_v3_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=50.5 |
| 2026-11-06 06:38:05 | tep_v3_board | episode_done | episode=tep_board_F08_r1; run=1; wall_s=293.8; group_top1=0.175; calls=341; unusable=3 |
| 2026-11-06 06:40:01 | tep_v3_board | episode_start | episode=tep_board_F09_r1; run=1; stem=tep_board_F09_r1_multi; chip_c=51.3 |
| 2026-11-06 06:44:32 | tep_v3_board | episode_done | episode=tep_board_F09_r1; run=1; wall_s=264.2; group_top1=0.0; calls=119; unusable=0 |
| 2026-11-06 06:46:45 | tep_v3_board | episode_start | episode=tep_board_F10_r1; run=1; stem=tep_board_F10_r1_multi; chip_c=50.0 |
| 2026-11-06 06:58:13 | tep_v3_board | episode_done | episode=tep_board_F10_r1; run=1; wall_s=681.5; group_top1=0.0; calls=235; unusable=0 |
| 2026-11-06 07:01:21 | tep_v3_board | episode_start | episode=tep_board_F11_r1; run=1; stem=tep_board_F11_r1_multi; chip_c=50.9 |
| 2026-11-06 07:12:50 | tep_v3_board | episode_done | episode=tep_board_F11_r1; run=1; wall_s=681.5; group_top1=0.0; calls=242; unusable=0 |
| 2026-11-06 07:16:33 | tep_v3_board | episode_start | episode=tep_board_F12_r1; run=1; stem=tep_board_F12_r1_multi; chip_c=48.4 |
| 2026-11-06 07:40:00 | tep_v3_board | episode_done | episode=tep_board_F12_r1; run=1; wall_s=1400.7; group_top1=0.955; calls=352; unusable=0 |
| 2026-11-06 07:43:08 | tep_v3_board | episode_start | episode=tep_board_F13_r1; run=1; stem=tep_board_F13_r1_multi; chip_c=50.2 |
| 2026-11-06 07:57:25 | tep_v3_board | episode_done | episode=tep_board_F13_r1; run=1; wall_s=849.7; group_top1=0.0; calls=252; unusable=0 |
| 2026-11-06 08:00:33 | tep_v3_board | episode_start | episode=tep_board_F14_r1; run=1; stem=tep_board_F14_r1_multi; chip_c=47.7 |
| 2026-11-06 08:14:42 | tep_v3_board | episode_done | episode=tep_board_F14_r1; run=1; wall_s=842.1; group_top1=0.956; calls=257; unusable=0 |
| 2026-11-06 08:17:30 | tep_v3_board | episode_start | episode=tep_board_F15_r1; run=1; stem=tep_board_F15_r1_multi; chip_c=50.9 |
| 2026-11-06 08:22:01 | tep_v3_board | episode_done | episode=tep_board_F15_r1; run=1; wall_s=264.2; group_top1=0.0; calls=119; unusable=0 |
| 2026-11-06 08:24:33 | tep_v3_board | episode_start | episode=tep_board_F16_r1; run=1; stem=tep_board_F16_r1_multi; chip_c=49.6 |
| 2026-11-06 08:36:09 | tep_v3_board | episode_done | episode=tep_board_F16_r1; run=1; wall_s=689.4; group_top1=0.787; calls=229; unusable=0 |
| 2026-11-06 08:39:08 | tep_v3_board | episode_start | episode=tep_board_F17_r1; run=1; stem=tep_board_F17_r1_multi; chip_c=50.0 |
| 2026-11-06 08:47:28 | tep_v3_board | episode_done | episode=tep_board_F17_r1; run=1; wall_s=492.2; group_top1=0.688; calls=172; unusable=0 |
| 2026-11-06 08:50:34 | tep_v3_board | episode_start | episode=tep_board_F18_r1; run=1; stem=tep_board_F18_r1_multi; chip_c=50.9 |
| 2026-11-06 09:06:58 | tep_v3_board | episode_done | episode=tep_board_F18_r1; run=1; wall_s=977.0; group_top1=0.17; calls=248; unusable=0 |
| 2026-11-06 09:09:29 | tep_v3_board | episode_start | episode=tep_board_F19_r1; run=1; stem=tep_board_F19_r1_multi; chip_c=50.9 |
| 2026-11-06 09:24:56 | tep_v3_board | episode_done | episode=tep_board_F19_r1; run=1; wall_s=919.8; group_top1=0.785; calls=287; unusable=0 |
| 2026-11-06 09:28:37 | tep_v3_board | episode_start | episode=tep_board_F20_r1; run=1; stem=tep_board_F20_r1_multi; chip_c=47.7 |
| 2026-11-06 09:39:56 | tep_v3_board | episode_done | episode=tep_board_F20_r1; run=1; wall_s=673.0; group_top1=0.526; calls=226; unusable=0 |
| 2026-11-06 09:43:04 | tep_v3_board | episode_start | episode=tep_board_N_r1; run=1; stem=tep_board_N_r1_multi; chip_c=50.9 |
| 2026-11-06 09:47:24 | tep_v3_board | episode_done | episode=tep_board_N_r1; run=1; wall_s=253.3; calls=115; unusable=0 |
| 2026-11-06 09:49:05 | tep_v3_board | episode_start | episode=tep_board_N_r2; run=1; stem=tep_board_N_r2_multi; chip_c=51.5 |
| 2026-11-06 09:52:03 | tep_v3_board | episode_done | episode=tep_board_N_r2; run=1; wall_s=171.2; calls=87; unusable=0 |
| 2026-11-06 09:52:04 | tep_v3_board | batch_end | status=all episodes done |
| 2026-11-06 10:07:39 | cranfield_dev_v3_shuffled | batch_start | command=scripts/benchmark.sh cranfield_dev_v3_shuffled cf_F1_1.2_air_line_blockage cf_F2_2.2_water_line_blockage cf_F3_3.2_top_separator_input_blockage cf_F4_4.2_open_direct_bypass cf_F5_5.1_slugging_conditions cf_F6_6.1_pressurization_of_the_2in_line --overlay configs/v3.yaml,configs/cranfield.yaml,configs/case_shuffled.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "3357ab8", "branch": "breadth-board-runs", "uncommitted_changes": false}; episodes=6; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/v3.yaml,configs/cranfield.yaml,configs/case_shuffled.yaml", "overlay_sha256": "985cadc924e47512", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf"}, "prompts_saved": true} |
| 2026-11-06 10:07:57 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=36.6 |
| 2026-11-06 10:11:25 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F1_1.2_air_line_blockage; run=1; wall_s=198.7; group_top1=0.514; calls=73; unusable=0 |
| 2026-11-06 10:14:31 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F2_2.2_water_line_blockage; run=1; stem=cf_F2_2.2_water_line_blockage_multi; chip_c=40.5 |
| 2026-11-06 10:16:16 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F2_2.2_water_line_blockage; run=1; wall_s=97.1; group_top1=0.412; calls=40; unusable=0 |
| 2026-11-06 10:18:44 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F3_3.2_top_separator_input_blockage; run=1; stem=cf_F3_3.2_top_separator_input_blockage_multi; chip_c=40.3 |
| 2026-11-06 10:23:50 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F3_3.2_top_separator_input_blockage; run=1; wall_s=297.4; group_top1=0.137; calls=119; unusable=0 |
| 2026-11-06 10:27:35 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F4_4.2_open_direct_bypass; run=1; stem=cf_F4_4.2_open_direct_bypass_multi; chip_c=40.5 |
| 2026-11-06 10:31:00 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F4_4.2_open_direct_bypass; run=1; wall_s=196.2; group_top1=0.152; calls=71; unusable=0 |
| 2026-11-06 10:34:25 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F5_5.1_slugging_conditions; run=1; stem=cf_F5_5.1_slugging_conditions_multi; chip_c=40.9 |
| 2026-11-06 10:40:28 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F5_5.1_slugging_conditions; run=1; wall_s=353.4; group_top1=0.311; calls=120; unusable=0 |
| 2026-11-06 10:46:09 | cranfield_dev_v3_shuffled | episode_start | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; stem=cf_F6_6.1_pressurization_of_the_2in_line_multi; chip_c=40.5 |
| 2026-11-06 10:47:20 | cranfield_dev_v3_shuffled | episode_done | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; wall_s=61.7; group_top1=0.857; calls=22; unusable=0 |
| 2026-11-06 10:47:21 | cranfield_dev_v3_shuffled | batch_end | status=all episodes done |
| 2026-11-06 10:54:29 | cranfield_dev_v3_bev | batch_start | command=scripts/benchmark.sh cranfield_dev_v3_bev cf_F1_1.2_air_line_blockage cf_F2_2.2_water_line_blockage cf_F3_3.2_top_separator_input_blockage cf_F4_4.2_open_direct_bypass cf_F5_5.1_slugging_conditions cf_F6_6.1_pressurization_of_the_2in_line --arch bev --overlay configs/bev3.yaml,configs/cranfield.yaml --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "2bc643c", "branch": "breadth-board-runs", "uncommitted_changes": false}; episodes=6; params={"arch": "bev", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev3.yaml,configs/cranfield.yaml", "overlay_sha256": "3198f7d4a3cbfa83", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev_device": "npu"} |
| 2026-11-06 10:54:54 | cranfield_dev_v3_bev | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_bev; chip_c=38.7 |
| 2026-11-06 10:58:57 | cranfield_dev_v3_bev | episode_done | episode=cf_F1_1.2_air_line_blockage; run=1; wall_s=233.5; group_top1=0.527; calls=124; unusable=0; decider={"calls": 52, "failed": 0, "rejected": 0} |
| 2026-11-06 11:04:56 | cranfield_dev_v3_bev | episode_start | episode=cf_F2_2.2_water_line_blockage; run=1; stem=cf_F2_2.2_water_line_blockage_bev; chip_c=41.3 |
| 2026-11-06 11:06:54 | cranfield_dev_v3_bev | episode_done | episode=cf_F2_2.2_water_line_blockage; run=1; wall_s=108.7; group_top1=0.471; calls=67; unusable=0; decider={"calls": 30, "failed": 0, "rejected": 0} |
| 2026-11-06 11:10:58 | cranfield_dev_v3_bev | episode_start | episode=cf_F3_3.2_top_separator_input_blockage; run=1; stem=cf_F3_3.2_top_separator_input_blockage_bev; chip_c=41.3 |
| 2026-11-06 11:17:14 | cranfield_dev_v3_bev | episode_done | episode=cf_F3_3.2_top_separator_input_blockage; run=1; wall_s=366.8; group_top1=0.157; calls=219; unusable=0; decider={"calls": 105, "failed": 0, "rejected": 0} |
| 2026-11-06 11:21:37 | cranfield_dev_v3_bev | episode_start | episode=cf_F4_4.2_open_direct_bypass; run=1; stem=cf_F4_4.2_open_direct_bypass_bev; chip_c=41.3 |
| 2026-11-06 11:25:41 | cranfield_dev_v3_bev | episode_done | episode=cf_F4_4.2_open_direct_bypass; run=1; wall_s=234.4; group_top1=0.202; calls=133; unusable=0; decider={"calls": 62, "failed": 0, "rejected": 0} |
| 2026-11-06 11:29:06 | cranfield_dev_v3_bev | episode_start | episode=cf_F5_5.1_slugging_conditions; run=1; stem=cf_F5_5.1_slugging_conditions_bev; chip_c=41.3 |
| 2026-11-06 11:35:40 | cranfield_dev_v3_bev | episode_done | episode=cf_F5_5.1_slugging_conditions; run=1; wall_s=385.1; group_top1=0.328; calls=195; unusable=0; decider={"calls": 75, "failed": 0, "rejected": 0} |
| 2026-11-06 11:40:22 | cranfield_dev_v3_bev | episode_start | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; stem=cf_F6_6.1_pressurization_of_the_2in_line_bev; chip_c=40.5 |
| 2026-11-06 11:41:42 | cranfield_dev_v3_bev | episode_done | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; wall_s=70.7; group_top1=0.8; calls=45; unusable=0; decider={"calls": 23, "failed": 0, "rejected": 0} |
| 2026-11-06 11:41:44 | cranfield_dev_v3_bev | batch_end | status=all episodes done |
| 2026-11-06 11:47:01 | cranfield_dev_bev_explain_skip | batch_start | command=scripts/benchmark.sh cranfield_dev_bev_explain_skip cf_F1_1.2_air_line_blockage cf_F2_2.2_water_line_blockage cf_F3_3.2_top_separator_input_blockage cf_F4_4.2_open_direct_bypass cf_F5_5.1_slugging_conditions cf_F6_6.1_pressurization_of_the_2in_line --overlay configs/bev_ideas.yaml,configs/cranfield.yaml --bev explain=on,clear_skip=on --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "716100d", "branch": "breadth-board-runs", "uncommitted_changes": false}; episodes=6; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml,configs/cranfield.yaml", "overlay_sha256": "7c2429a641c94086", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on,clear_skip=on", "bev_device": "npu"} |
| 2026-11-06 11:47:25 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=37.8 |
| 2026-11-06 11:49:21 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 11:49:21 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 11:49:36 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=15 |
| 2026-11-06 11:52:37 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=39.7 |
| 2026-11-06 11:52:58 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 11:52:58 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 11:53:34 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=35 |
| 2026-11-06 11:56:28 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=39.5 |
| 2026-11-06 11:57:14 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 11:57:14 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 11:57:29 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=15 |
| 2026-11-06 12:13:40 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=39.5 |
| 2026-11-06 12:14:02 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 12:14:02 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 12:14:17 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=15 |
| 2026-11-06 12:32:03 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=48.2 |
| 2026-11-06 12:32:26 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 12:32:26 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 12:32:36 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=10 |
| 2026-11-06 12:50:19 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=48.2 |
| 2026-11-06 12:50:40 | cranfield_dev_bev_explain_skip | episode_failed | episode=cf_F1_1.2_air_line_blockage; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 12:50:40 | cranfield_dev_bev_explain_skip | board_lost | episode=cf_F1_1.2_air_line_blockage |
| 2026-11-06 12:51:10 | cranfield_dev_bev_explain_skip | board_back | episode=cf_F1_1.2_air_line_blockage; waited_s=30 |
| 2026-11-06 13:08:49 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F1_1.2_air_line_blockage; run=1; stem=cf_F1_1.2_air_line_blockage_multi; chip_c=65.1 |
| 2026-11-06 13:09:20 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F1_1.2_air_line_blockage; run=1; wall_s=24.1; group_top1=0.5; calls=139; unusable=3; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 3}, "explain": {"calls": 65, "failed": 0, "rejected": 0, "used": 65}} |
| 2026-11-06 13:26:58 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F2_2.2_water_line_blockage; run=1; stem=cf_F2_2.2_water_line_blockage_multi; chip_c=52.5 |
| 2026-11-06 13:28:18 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F2_2.2_water_line_blockage; run=1; wall_s=72.7; group_top1=0.324; calls=69; unusable=0; bev_ideas={"explain": {"calls": 29, "failed": 0, "rejected": 0, "used": 29}} |
| 2026-11-06 13:45:51 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F3_3.2_top_separator_input_blockage; run=1; stem=cf_F3_3.2_top_separator_input_blockage_multi; chip_c=50.2 |
| 2026-11-06 13:49:48 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F3_3.2_top_separator_input_blockage; run=1; wall_s=227.5; group_top1=0.041; calls=182; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 28}, "explain": {"calls": 78, "failed": 0, "rejected": 0, "used": 78}} |
| 2026-11-06 13:53:52 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F4_4.2_open_direct_bypass; run=1; stem=cf_F4_4.2_open_direct_bypass_multi; chip_c=39.7 |
| 2026-11-06 13:56:32 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F4_4.2_open_direct_bypass; run=1; wall_s=151.7; group_top1=0.051; calls=146; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}, "explain": {"calls": 65, "failed": 0, "rejected": 0, "used": 65}} |
| 2026-11-06 14:00:17 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F5_5.1_slugging_conditions; run=1; stem=cf_F5_5.1_slugging_conditions_multi; chip_c=39.3 |
| 2026-11-06 14:04:20 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F5_5.1_slugging_conditions; run=1; wall_s=234.3; group_top1=0.328; calls=233; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 2}, "explain": {"calls": 115, "failed": 0, "rejected": 0, "used": 115}} |
| 2026-11-06 14:08:23 | cranfield_dev_bev_explain_skip | episode_start | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; stem=cf_F6_6.1_pressurization_of_the_2in_line_multi; chip_c=39.7 |
| 2026-11-06 14:09:06 | cranfield_dev_bev_explain_skip | episode_done | episode=cf_F6_6.1_pressurization_of_the_2in_line; run=1; wall_s=33.6; group_top1=0.943; calls=37; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 18, "failed": 0, "rejected": 0, "used": 18}} |
| 2026-11-06 14:09:08 | cranfield_dev_bev_explain_skip | batch_end | status=all episodes done |
| 2026-11-06 14:14:09 | tep_bev_explain_skip_board | batch_start | command=scripts/benchmark.sh tep_bev_explain_skip_board tep_board_F01_r1 tep_board_F02_r1 tep_board_F03_r1 tep_board_F04_r1 tep_board_F05_r1 tep_board_F06_r1 tep_board_F07_r1 tep_board_F08_r1 tep_board_F09_r1 tep_board_F10_r1 tep_board_F11_r1 tep_board_F12_r1 tep_board_F13_r1 tep_board_F14_r1 tep_board_F15_r1 tep_board_F16_r1 tep_board_F17_r1 tep_board_F18_r1 tep_board_F19_r1 tep_board_F20_r1 tep_board_N_r1 tep_board_N_r2 --overlay configs/bev_ideas.yaml,configs/tep.yaml --bev explain=on,clear_skip=on --trace-to /home/harsha/qidk_logs/current.trace.log; git={"commit": "ffc4312", "branch": "breadth-board-runs", "uncommitted_changes": false}; episodes=22; params={"arch": "multi", "mode": "lockstep", "tick_s": null, "overlay": "configs/bev_ideas.yaml,configs/tep.yaml", "overlay_sha256": "ad0e05360a75d057", "merge_rule": "hybrid", "backend": "llamaserver", "models": {"npu": "Llama-3.2-3B-Instruct-Q4_0-pure-embq8.gguf", "cpu": "gemma-3-1b-it-qat-Q4_0-pure-embq8.gguf", "bev": "bev-decider-0.4B-backbone-Q8_0.gguf"}, "prompts_saved": true, "bev": "explain=on,clear_skip=on", "bev_device": "npu"} |
| 2026-11-06 14:14:32 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=36.4 |
| 2026-11-06 14:16:15 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:16:15 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:16:30 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=15 |
| 2026-11-06 14:20:07 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=39.5 |
| 2026-11-06 14:20:15 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:20:15 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:20:40 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=25 |
| 2026-11-06 14:21:16 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=38.7 |
| 2026-11-06 14:21:27 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:21:27 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:22:12 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=45 |
| 2026-11-06 14:22:30 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=38.4 |
| 2026-11-06 14:22:39 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:22:39 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:23:34 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=55 |
| 2026-11-06 14:23:53 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=39.3 |
| 2026-11-06 14:35:09 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:35:09 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:35:29 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=20 |
| 2026-11-06 14:42:29 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=39.3 |
| 2026-11-06 14:42:44 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F01_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 14:42:44 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F01_r1 |
| 2026-11-06 14:43:24 | tep_bev_explain_skip_board | board_back | episode=tep_board_F01_r1; waited_s=40 |
| 2026-11-06 14:43:45 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F01_r1; run=1; stem=tep_board_F01_r1_multi; chip_c=39.0 |
| 2026-11-06 14:46:04 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F01_r1; run=1; wall_s=128.5; group_top1=0.218; calls=677; unusable=3; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 319, "failed": 0, "rejected": 0, "used": 319}} |
| 2026-11-06 14:49:10 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F02_r1; run=1; stem=tep_board_F02_r1_multi; chip_c=39.0 |
| 2026-11-06 15:01:46 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F02_r1; run=1; wall_s=745.9; group_top1=0.159; calls=630; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 296, "failed": 0, "rejected": 0, "used": 296}} |
| 2026-11-06 15:06:48 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F03_r1; run=1; stem=tep_board_F03_r1_multi; chip_c=39.0 |
| 2026-11-06 15:08:53 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F03_r1; run=1; wall_s=115.8; group_top1=0.0; calls=145; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 38, "failed": 0, "rejected": 0, "used": 38}} |
| 2026-11-06 15:12:19 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F04_r1; run=1; stem=tep_board_F04_r1_multi; chip_c=39.0 |
| 2026-11-06 15:16:22 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F04_r1; run=1; wall_s=234.1; group_top1=0.792; calls=297; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 39}, "explain": {"calls": 110, "failed": 0, "rejected": 0, "used": 110}} |
| 2026-11-06 15:20:26 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F05_r1; run=1; stem=tep_board_F05_r1_multi; chip_c=39.3 |
| 2026-11-06 15:31:03 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F05_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 15:31:03 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F05_r1 |
| 2026-11-06 15:32:09 | tep_bev_explain_skip_board | board_back | episode=tep_board_F05_r1; waited_s=65 |
| 2026-11-06 15:33:44 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F05_r1 |
| 2026-11-06 18:53:41 | tep_bev_explain_skip_board | board_back | episode=tep_board_F05_r1; waited_s=11965 |
| 2026-11-06 18:53:59 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F05_r1; run=1; stem=tep_board_F05_r1_multi; chip_c=35.2 |
| 2026-11-06 18:54:10 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F05_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 18:54:10 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F05_r1 |
| 2026-11-06 18:55:10 | tep_bev_explain_skip_board | board_back | episode=tep_board_F05_r1; waited_s=60 |
| 2026-11-06 18:55:31 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F05_r1; run=1; stem=tep_board_F05_r1_multi; chip_c=35.9 |
| 2026-11-06 19:00:00 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F05_r1; run=1; wall_s=258.5; group_top1=0.0; calls=683; unusable=1; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 9}, "explain": {"calls": 321, "failed": 0, "rejected": 0, "used": 321}} |
| 2026-11-06 19:04:23 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=39.3 |
| 2026-11-06 19:06:24 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 19:06:24 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 19:07:30 | tep_bev_explain_skip_board | board_back | episode=tep_board_F06_r1; waited_s=65 |
| 2026-11-06 19:12:20 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=39.0 |
| 2026-11-06 19:12:28 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 19:12:28 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 19:13:18 | tep_bev_explain_skip_board | board_back | episode=tep_board_F06_r1; waited_s=50 |
| 2026-11-06 19:13:57 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=39.0 |
| 2026-11-06 19:14:12 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 19:14:12 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 19:15:12 | tep_bev_explain_skip_board | board_back | episode=tep_board_F06_r1; waited_s=60 |
| 2026-11-06 19:16:07 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=38.4 |
| 2026-11-06 19:16:15 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F06_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 19:16:15 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F06_r1 |
| 2026-11-06 19:18:40 | tep_bev_explain_skip_board | board_back | episode=tep_board_F06_r1; waited_s=145 |
| 2026-11-06 19:19:17 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F06_r1; run=1; stem=tep_board_F06_r1_multi; chip_c=38.6 |
| 2026-11-06 19:32:46 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F06_r1; run=1; wall_s=799.8; group_top1=0.421; calls=668; unusable=2; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 316, "failed": 0, "rejected": 0, "used": 316}} |
| 2026-11-06 19:38:49 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F07_r1; run=1; stem=tep_board_F07_r1_multi; chip_c=39.3 |
| 2026-11-06 19:56:53 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F07_r1; run=1; wall_s=1073.5; group_top1=0.088; calls=696; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 5}, "explain": {"calls": 326, "failed": 0, "rejected": 0, "used": 326}} |
| 2026-11-06 20:03:51 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F08_r1; run=1; stem=tep_board_F08_r1_multi; chip_c=39.3 |
| 2026-11-06 20:19:11 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F08_r1; run=1; wall_s=909.6; group_top1=0.014; calls=634; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 295, "failed": 0, "rejected": 0, "used": 295}} |
| 2026-11-06 20:25:14 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F09_r1; run=1; stem=tep_board_F09_r1_multi; chip_c=39.1 |
| 2026-11-06 20:27:29 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F09_r1; run=1; wall_s=125.8; group_top1=0.0; calls=149; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 9}, "explain": {"calls": 39, "failed": 0, "rejected": 0, "used": 39}} |
| 2026-11-06 20:31:33 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F10_r1; run=1; stem=tep_board_F10_r1_multi; chip_c=39.3 |
| 2026-11-06 20:38:03 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F10_r1; run=1; wall_s=380.1; group_top1=0.0; calls=405; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 5}, "explain": {"calls": 176, "failed": 0, "rejected": 0, "used": 176}} |
| 2026-11-06 20:44:05 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F11_r1; run=1; stem=tep_board_F11_r1_multi; chip_c=39.3 |
| 2026-11-06 20:46:40 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F11_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 20:46:40 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F11_r1 |
| 2026-11-06 20:47:10 | tep_bev_explain_skip_board | board_back | episode=tep_board_F11_r1; waited_s=30 |
| 2026-11-06 20:52:39 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F11_r1; run=1; stem=tep_board_F11_r1_multi; chip_c=39.5 |
| 2026-11-06 20:52:48 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F11_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 20:52:48 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F11_r1 |
| 2026-11-06 20:53:03 | tep_bev_explain_skip_board | board_back | episode=tep_board_F11_r1; waited_s=15 |
| 2026-11-06 20:54:19 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F11_r1; run=1; stem=tep_board_F11_r1_multi; chip_c=39.3 |
| 2026-11-06 20:58:16 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F11_r1; run=1; wall_s=226.7; group_top1=0.0; calls=389; unusable=1; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 9}, "explain": {"calls": 154, "failed": 0, "rejected": 0, "used": 154}} |
| 2026-11-06 21:03:20 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F12_r1; run=1; stem=tep_board_F12_r1_multi; chip_c=39.5 |
| 2026-11-06 21:07:08 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F12_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 21:07:08 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F12_r1 |
| 2026-11-06 21:08:58 | tep_bev_explain_skip_board | board_back | episode=tep_board_F12_r1; waited_s=110 |
| 2026-11-06 21:15:04 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F12_r1; run=1; stem=tep_board_F12_r1_multi; chip_c=38.6 |
| 2026-11-06 21:15:13 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F12_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 21:15:13 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F12_r1 |
| 2026-11-06 21:16:39 | tep_bev_explain_skip_board | board_back | episode=tep_board_F12_r1; waited_s=85 |
| 2026-11-06 21:16:59 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F12_r1; run=1; stem=tep_board_F12_r1_multi; chip_c=39.5 |
| 2026-11-06 21:27:38 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F12_r1; run=1; wall_s=628.1; group_top1=0.594; calls=653; unusable=1; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 309, "failed": 0, "rejected": 0, "used": 309}} |
| 2026-11-06 21:33:41 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F13_r1; run=1; stem=tep_board_F13_r1_multi; chip_c=39.3 |
| 2026-11-06 21:41:10 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F13_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 21:41:10 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F13_r1 |
| 2026-11-06 21:41:25 | tep_bev_explain_skip_board | board_back | episode=tep_board_F13_r1; waited_s=15 |
| 2026-11-06 21:49:19 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F13_r1; run=1; stem=tep_board_F13_r1_multi; chip_c=39.5 |
| 2026-11-06 21:49:30 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F13_r1; run=1; exit=1; last=http.client.RemoteDisconnected: Remote end closed connection without response; board_connection_lost=True |
| 2026-11-06 21:49:30 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F13_r1 |
| 2026-11-06 21:51:11 | tep_bev_explain_skip_board | board_back | episode=tep_board_F13_r1; waited_s=100 |
| 2026-11-06 21:51:47 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F13_r1; run=1; stem=tep_board_F13_r1_multi; chip_c=39.1 |
| 2026-11-06 21:53:03 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F13_r1; run=1; wall_s=65.8; group_top1=0.0; calls=417; unusable=1; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 175, "failed": 0, "rejected": 0, "used": 175}} |
| 2026-11-06 21:54:35 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F14_r1; run=1; stem=tep_board_F14_r1_multi; chip_c=39.3 |
| 2026-11-06 22:03:32 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F14_r1; run=1; wall_s=526.3; group_top1=0.553; calls=464; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 4}, "explain": {"calls": 209, "failed": 0, "rejected": 0, "used": 209}} |
| 2026-11-06 22:09:13 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F15_r1; run=1; stem=tep_board_F15_r1_multi; chip_c=39.3 |
| 2026-11-06 22:11:22 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F15_r1; run=1; wall_s=120.6; group_top1=0.0; calls=152; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 7}, "explain": {"calls": 40, "failed": 0, "rejected": 0, "used": 40}} |
| 2026-11-06 22:15:47 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F16_r1; run=1; stem=tep_board_F16_r1_multi; chip_c=39.0 |
| 2026-11-06 22:22:18 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F16_r1; run=1; wall_s=381.4; group_top1=0.695; calls=391; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 14}, "explain": {"calls": 176, "failed": 0, "rejected": 0, "used": 176}} |
| 2026-11-06 22:28:19 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F17_r1; run=1; stem=tep_board_F17_r1_multi; chip_c=39.0 |
| 2026-11-06 22:32:55 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F17_r1; run=1; wall_s=266.3; group_top1=0.581; calls=281; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 114, "failed": 0, "rejected": 0, "used": 114}} |
| 2026-11-06 22:37:20 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F18_r1; run=1; stem=tep_board_F18_r1_multi; chip_c=39.3 |
| 2026-11-06 22:47:03 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F18_r1; run=1; wall_s=574.2; group_top1=0.17; calls=437; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 8}, "explain": {"calls": 198, "failed": 0, "rejected": 0, "used": 198}} |
| 2026-11-06 22:52:07 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F19_r1; run=1; stem=tep_board_F19_r1_multi; chip_c=39.3 |
| 2026-11-06 22:55:41 | tep_bev_explain_skip_board | episode_failed | episode=tep_board_F19_r1; run=1; exit=1; last=bench.call_journal.BoardConnectionLost: Connection refused: bev_explain@bev tick 224: error connection dropped: RemoteDisconnected('Remote end closed connection without response') (board connection lost; not scored); board_connection_lost=True |
| 2026-11-06 22:55:41 | tep_bev_explain_skip_board | board_lost | episode=tep_board_F19_r1 |
| 2026-11-07 03:45:58 | tep_bev_explain_skip_board | board_back | episode=tep_board_F19_r1; waited_s=17395 |
| 2026-11-07 03:46:21 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F19_r1; run=1; stem=tep_board_F19_r1_multi; chip_c=36.4 |
| 2026-11-07 03:52:04 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F19_r1; run=1; wall_s=333.9; group_top1=0.563; calls=487; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 15}, "explain": {"calls": 215, "failed": 0, "rejected": 0, "used": 215}} |
| 2026-11-07 03:56:26 | tep_bev_explain_skip_board | episode_start | episode=tep_board_F20_r1; run=1; stem=tep_board_F20_r1_multi; chip_c=39.0 |
| 2026-11-07 04:02:37 | tep_bev_explain_skip_board | episode_done | episode=tep_board_F20_r1; run=1; wall_s=362.4; group_top1=0.377; calls=357; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 11}, "explain": {"calls": 140, "failed": 0, "rejected": 0, "used": 140}} |
| 2026-11-07 04:07:38 | tep_bev_explain_skip_board | episode_start | episode=tep_board_N_r1; run=1; stem=tep_board_N_r1_multi; chip_c=39.0 |
| 2026-11-07 04:09:34 | tep_bev_explain_skip_board | episode_done | episode=tep_board_N_r1; run=1; wall_s=106.6; calls=141; unusable=0; bev_ideas={"clear_skip": {"calls": 0, "failed": 0, "rejected": 0, "used": 10}, "explain": {"calls": 36, "failed": 0, "rejected": 0, "used": 36}} |
| 2026-11-07 04:12:20 | tep_bev_explain_skip_board | episode_start | episode=tep_board_N_r2; run=1; stem=tep_board_N_r2_multi; chip_c=39.3 |
| 2026-11-07 04:13:52 | tep_bev_explain_skip_board | episode_done | episode=tep_board_N_r2; run=1; wall_s=83.1; calls=98; unusable=0; bev_ideas={"explain": {"calls": 11, "failed": 0, "rejected": 0, "used": 11}} |
| 2026-11-07 04:13:54 | tep_bev_explain_skip_board | batch_end | status=all episodes done |
