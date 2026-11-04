# Failures in AI product video, and fixes

| Failure | Why | Fix |
|---|---|---|
| Garbled label, invented words ("HOTEL BATHIVAL") | Small text fails first; spins force the model to invent unseen sides | Clean straight-on reference; spell the label in the prompt; keep the camera still on the label or push in; composite the real label; 100% check |
| Logo warps on a spin | Unseen sides are invented | `qwen_angles` for real side views as refs/keyframes; `pixelcut_looping_video` (spin) for loops; `minimax_h3_max_camera_controls` for exact orbits; slides and parallax instead of 360° |
| Fingers through the bottle, extra fingers, hand over the label | Hand-object contact is the hardest physics | First frame from `bria_fibo_edit_1_5_product_holding`; hands at the edges; one hand anchored on the box base; "five fingers per hand" |
| Wrong scale | No size cue | A hand or a known object in the hero still; state the size ("30 ml bottle fits in the palm"). TikTok Shop bans AI that changes size |
| Liquid, foam, glass look like a defect | They change with every light move | Locked camera, only the liquid moves; re-edit only the bad shot (`omni_flash_1_1` edit, `seedance_2_5` omni-reference edit) |
| Invented props (steam, splashes, coffee) | Cinematic priors | An explicit "Add no hand, person, prop, ingredient, droplet, splash, mist…" list; less motion |
| Storyboard panels leak into the video | The sheet is a visual reference | "follow its shot order, never show its panels, numbers or text" + negative list |
| Captions or text added by the model | Model habit | "No subtitles, captions, extra logos or watermarks"; add captions in the edit |
| Random music fills silence (Seedance) | Empty audio slot | "No background music" / "Natural ASMR only" |
| First/last-frame clip invents a camera move | The gap is free | Lock the camera in both frames, or use reference mode |
| Product does more than it can (fake fizz, instant results) | Prompt asked for drama | Remove it: misleading under TikTok Shop and FTC rules |
| ~1 keeper in 8 renders (one agency) | Normal variance | Generate ≥4 candidates of a hard shot on a cheap model; count cost per accepted clip, not per render |

Sources: @abxxai, @Strength04_X, @yourPlugAI, @qaqashish on X; [Masonry](https://masonry.so/blog/best-ai-video-model-for-product-ads); AI Film Contests product-accuracy guide; TikTok Shop Seller University via [ppc.land](https://ppc.land/tiktok-shops-quality-rules-ban-ai-voices-and-still-images-from-lives/).
