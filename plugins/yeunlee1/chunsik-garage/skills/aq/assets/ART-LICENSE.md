# Character art terms / 캐릭터 그림 이용 조건

The code in this repository is MIT licensed (see `LICENSE`). The character art in this folder is **not** covered by the MIT license.

You may share the art as it appears in the cards, result pages, and screenshots that this tool makes. You may not take the art out of them and use it elsewhere.

이 저장소의 코드는 MIT다(`LICENSE`). 이 폴더의 캐릭터 그림은 MIT가 아니다.

이 도구가 만든 카드, 결과 화면, 소개 캡처에 든 그림은 그대로 공유해도 된다. 그림만 떼어 다른 데 쓰는 것은 허락하지 않는다.

| File | Size | Used for |
|---|---|---|
| `scene-1.webp` … `scene-5.webp` | 512×512 | The scene next to the AQ score, one per grade tier (1 lowest to 5 highest), and the share card |
| `scene-few-records.webp` | 512×512 | The scene when no AQ was given (not enough records yet) |
| `scene-unreadable.webp` | 512×512 | The scene when no AQ was given and some records could not be read |
| `face.webp` | 128×128 | Chunsik's face next to the brand name and on the share card |
| `sticker-good.webp` | 128×128 | Chunsam's sticker next to "Doing well" |
| `sticker-fix.webp` | 128×128 | Chunsik's sticker next to "To fix" when there is something to fix |
| `sticker-done.webp` | 128×128 | Chunsik's sticker next to "To fix" when there is nothing to fix |
| `icon.png` | 512×512 | The plugin icon in plugin directories (PNG, because the Claude plugin directory does not take WebP) |
| `composer-icon.png` | 128×128 | The Codex plugin icon in the composer, scaled down from `icon.png` |
| `logo.png` | 192×192 | The Codex plugin icon in listings, scaled down from `icon.png` |

`scripts/make-assets.py` makes these files from the original drawings, which are not in this repository.

The same terms cover `docs/images/hero.png` (1280×640), the picture at the top of the README that is also the repository's link preview. `scripts/make-hero.py` makes it from its original drawing.

README 맨 위 그림이자 저장소 링크 미리보기 그림인 `docs/images/hero.png`(1280×640)도 같은 조건이다. `scripts/make-hero.py`가 원본 그림으로 만든다.
