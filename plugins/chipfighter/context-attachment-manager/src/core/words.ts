// Purpose: the text for the model (v0.11: moved here from rewrite.ts unchanged, docs/v0.11/plan.md): placeholders,
// notes, labels, lists, and the words of the fetch tool, in Chinese and English. Every platform and request format
// uses the same words; where a platform needs its own (Claude's notes after a message, Codex's compaction note), the
// function says so. The history of each wording is in the comments next to it.
// v0.1 — placeholders say the image was seen when it appeared and is left out now by the user's choice, so the model
// keeps trusting what it said about it (user report 2026-09-25).
// v0.1-14 — in the user's language (Codex's interface language, language.ts): the Chinese wording is the one tested on
// 2026-09-25; the English one says the same and is checked by the same self-test (v01-placeholder-selftest.ts --lang en).
// v0.1-24 — how to ask for an image back is spelled out, for every GPT-6 model (self-tests with CAM_TEST_MODEL).
// v0.1-25 — once anything is left out, each image still sent carries its id, and the note says a checked image is back
// in its old place: GPT-6 Luna looked for it in the newest message and said it could not see it (user 2026-09-28).
// v0.3 — automatic selection (user 2026-10-06): images from earlier turns that are not pinned are left out, in their own
// wording, and the model fetches what it needs with cam_view_image (whose words are here too, as text for the model).
// A copy it fetched is sent in that turn only. Drafts of this wording were tried on the three GPT-6 models in Chinese
// and English before it was built (spike/src/auto-fetch-selftest.ts).
// v0.8 (docs/v0.8/plan.md) — the model writes a feature line for each new image and notes the user's ratings, as record
// lines in its replies (notes.ts); a placeholder carries them, so the model still tells the images apart after a
// compaction. For that a feature line note goes before the turn of the first image, and every image sent says its id,
// also the ones new in this turn. The second line of a placeholder is shorter, offsetting the added text.
// Input: what is known of an image (Described), the language. Output: strings.

import { FETCHED_STATE, type ImageKind } from "./images.ts";
import type { Lang } from "./lang.ts";
import type { Notes, Rating } from "./notes.ts";

// notes (v0.8): what the model noted about the image, shown in its placeholder. awaiting (v0.10): an image of an
// interrupted turn sent once more for its feature line (thread-index.ts, awaitingLine); its label says so.
// v0.12: now, an image of the current turn left out in it (core/session.ts inTurnOut): its heading says 本轮.
export type Described = { id: string; name: string | null; label: string | null; kind: ImageKind; turn: number | null; width: number | null; height: number | null; notes?: Notes; awaiting?: boolean; now?: boolean };

type FetchWords = { title: string; description: string; ids: string; missing: (id: string) => string; unavailable: (id: string) => string; off: string };
// v0.13, Claude Code only (docs/design.md §14): the fetch tool also gets PDF pages back.
type ClaudeFetchWords = { description: string; ids: string; pages: string; pdfUnavailable: (id: string) => string };
// v0.13, Claude Code only: a PDF read in an earlier turn, the notes after the message holding it, the pages the model
// fetched (as the fetch tool marks them, and as the engine puts them in).
type PdfWords = {
  unnamed: string; pages: (count: number) => string; kind: (pages: number, textPages: number) => string; turn: (n: number) => string;
  heading: (id: string, fields: string[]) => string; said: (start: string) => string; ask: (id: string) => string;
  listItem: (id: string, name: string) => string; listSeparator: string;
  fullNote: string; here: (list: string) => string;
  marker: (id: string, name: string, pages: string | null) => string; some: (pages: string, total: number | null) => string; whole: (total: number | null) => string; rest: (turn: number) => string;
  fetched: (id: string, fields: string[]) => string; rangeSeparator: string;
};
type Words = {
  kind: Record<ImageKind, string>; unnamed: string; turn: (n: number) => string; thisTurn: string; newImage: string;
  // v0.10: the source in a compact line (compactLine), shorter.
  kindShort: Record<ImageKind, string>; sameShort: (id: string) => string;
  omitted: string; notRepeated: string; included: string; separator: string;
  // v0.10: the label of an image sent once more for its feature line (Described.awaiting). v0.12, Claude: a short note
  // after the turn's own message naming them (Haiku 5.5 left them out with the label alone, 2026-11-22).
  includedAwaiting: string; awaitingNote: (ids: string[]) => string;
  heading: (id: string, label: string | null, state: string, fields: string[]) => string;
  plain: (id: string) => string; duplicate: (id: string, where: string) => string; note: string;
  autoPlain: (id: string) => string; autoNote: string; copy: (id: string) => string; fetch: FetchWords;
  // v0.4, Claude Code only (anthropic-messages/rewrite.ts): what the note adds about tool results, and the short note that follows
  // each message holding omitted images, naming them.
  toolNote: string; here: (list: string) => string; hereAuto: (list: string) => string; listItem: (id: string, name: string | null, kind: string) => string;
  // v0.5, Claude Code only: after a compaction summary, the images from before it, which of them are not sent this
  // time, and how to get one back. v0.10: how many and their ids, no longer listed; those not sent are one line each
  // in a list after the summary (compactHeader, compactLine).
  compacted: (count: number, range: string, missing: number, auto: boolean) => string;
  compactHeader: (count: number) => string;
  // v0.10, Codex: the images its compaction did not keep, put back after it: how many, how many sent as originals.
  codexCompacted: (count: number, resent: number, auto: boolean) => string;
  // v0.8: how to write feature lines and note ratings; the placeholder's line with them; how long each may be shown.
  featureNote: string; notes: (line: string | null, ratings: Rating[]) => string;
  claudeFetch: ClaudeFetchWords; pdf: PdfWords;
};

// The image sits in the history, so the model concludes it never saw it and takes back what it said about it (user
// report 2026-09-25). Saying otherwise inside the placeholder did not help: it is user content, which the model does
// not take as proof. So the explanation goes once into a developer message, before the turn where the first omitted
// image appeared, and each placeholder only points to it.
const WORDS: Record<Lang, Words> = {
  zh: {
    kind: { upload: "用户上传", view: "工具查看的图片", generated: "生成的图片", tool: "工具结果里的图片" },
    kindShort: { upload: "上传", view: "查看", generated: "生成", tool: "工具" },
    sameShort: (id) => `同 ${id}`,
    unnamed: "未命名",
    turn: (n) => `第 ${n} 轮`,
    thisTurn: "本轮",
    newImage: "（新图片）",
    omitted: "已省略",
    notRepeated: "未重复提供",
    included: "已提供",
    includedAwaiting: "已提供，还没有特征行",
    awaitingNote: (ids) => `特征行说明：${ids.join("、")} 在它们那一轮没有写上特征行，原图这一轮再提供一次（前面标着“已提供，还没有特征行”）。请在这一轮最后那条回复的开头，也给它们各写一行。`,
    separator: "，",
    heading: (id, label, state, fields) => `[图片 ${id}${label ? `（${label}）` : ""} ${state}｜${fields.join("｜")}]`,
    // v0.8: shorter; the context management note says why the image is left out (it was "原图被用户省略以节省上下文，情况
    // 见前面的“上下文管理说明”；需要重新看这张图时，在回复里写出“需要 IMG-xxx”。").
    plain: (id) => `需要重看时，在回复里写“需要 ${id}”。`,
    duplicate: (id, where) => `这张图和 ${id}（${where}）内容完全相同，那一条在本次请求里照常提供，请直接参考那一条。`,
    note: [
      "上下文管理说明（来自用户安装的上下文素材管理工具）：为了节省上下文，用户取消勾选了这个任务里的部分图片。后面的对话里，这些图片原来的位置被换成了“[图片 IMG-xxx 已省略…]”这样的占位文字；仍在提供的图片前面标着“[图片 IMG-xxx 已提供…]”，紧接着就是原图。",
      "这些图片在它们出现的那一轮真实存在，你当时收到并看过；你之前对它们的描述，以及据此做出的判断，都是看着原图做出的，仍然有效。不要因为现在看不到，就认为之前的回答是猜测或错误，也不要收回或道歉。",
      "被问到现在能不能看到某张被省略的图片时，如实说明现在看不到（被用户省略了），并说明之前的描述仍然有效。现在看不到画面，就不要补充之前没说过的细节。需要重新看某张图时，在回复里原样写出“需要 IMG-xxx”（几张就写“需要 IMG-002、IMG-003”）：工具靠这几个字认出你要的图。用户重新勾选后，原图会回到它在对话里原来的位置：那里的占位文字换成“[图片 IMG-xxx 已提供…]”和原图；它不会出现在用户的新消息里，所以不要让用户重新上传或附上图片。不要自己用工具去读取这些图片。",
      "标着“[图片 IMG-xxx 已提供…]”的图片现在就在你面前，即使它之前被省略过、或者正是你要过的图：被问到它时，直接看图回答，不要说看不到。",
    ].join("\n"),
    autoPlain: (id) => `需要原图时调用 cam_view_image，传入“${id}”。`,
    // 2026-11-01, long-task eval (Haiku 5.5, effort low): after a compaction the model stopped reading the files the
    // user named, five turns running ("没有收到图片内容，只有文字说明"): "do not read image files with other tools" was
    // taken for every image. It now says the omitted ones, and that new images are looked at as usual.
    autoNote: [
      "上下文管理说明（来自用户安装的上下文素材管理工具）：这个任务开着“自动选图”。为了节省上下文，之前各轮的图片默认不再随请求提供，后面的对话里，它们原来的位置换成了“[图片 IMG-xxx 已省略…]”这样的占位文字；本轮新出现的图片照常提供，用户固定发送的图片也照常提供，前面标着“[图片 IMG-xxx 已提供…]”，紧接着就是原图。",
      "这些图片在它们出现的那一轮真实存在，你当时收到并看过；你之前对它们的描述，以及据此做出的判断，都是看着原图做出的，仍然有效。不要因为现在看不到，就认为之前的回答是猜测或错误，也不要收回或道歉。",
      "回答需要看某张被省略的图片、而你之前说过的内容不够用时，调用 cam_view_image 工具，传入它的编号（几张就一次传几个），原图会出现在这次的工具结果里，前面标着“[图片 IMG-xxx 取回的原图…]”，拿到后看图回答。之前说过的内容够用时，不要调用。现在看不到的画面细节，不要猜测或补充；不要让用户重新上传图片，也不要用其他工具去读取这些被省略的图片的文件；用户新让你看的图片不受影响，照常去看。",
      "用 cam_view_image 取回的图片只在本轮提供，下一轮又会换回占位文字；之后还需要时，再调用一次。标着“已提供”或“取回的原图”的图片现在就在你面前：被问到它时，直接看图回答，不要说看不到。",
    ].join("\n"),
    copy: (id) => `[${id} 的原图：模型当时用 cam_view_image 取回，只在那一轮提供，现在已省略]`,
    // v0.4: in Claude Code desktop tests (Haiku 5.5, 2026-10-09) the model read a placeholder inside a Read result as
    // what the tool had returned, said it had never seen the image and took back its correct description; the same
    // words inside the tool result were not believed ("I should not follow the placeholder"). With the note right after
    // the message holding the image, it answered as intended. So each such message is followed by a short note.
    // 2026-10-10, Haiku 5.5, tool images, 3 runs per language: it kept its answers and guessed nothing, but asked for
    // the image by number in 2 of 3 Chinese runs (as an option) and in no English run; a question about a detail it
    // never described got "I can't answer that". The note now says when to write "需要 IMG-xxx", and why.
    toolNote: "工具结果里的图片也一样：那次工具调用当时返回的是原图，你当时看到了；工具结果里的占位文字是后来才换上的，不是工具当时的返回。",
    here: (list) => `上下文管理说明：上面这条消息里的 ${list} 当时是原图，你当时看过；你之前对它们的描述和据此做出的判断仍然有效，不要收回，也不要说成是猜测或编造。那里的占位文字是这次请求才换上的，不是当时的内容。现在你看不到它们：被问到时，如实说现在看不到（被用户省略了），不要补充之前没说过的细节。问题得看其中某张图才能回答时，不要只说答不了，在回复里单独写一行“需要 IMG-xxx”（写出编号，几张就都写上）：用户看到这一行才知道该勾回哪张图，勾回后原图回到原处，你就能看着回答。`,
    hereAuto: (list) => `上下文管理说明：上面这条消息里的 ${list} 当时是原图，你当时看过；你之前对它们的描述和据此做出的判断仍然有效，不要收回，也不要说成是猜测或编造。那里的占位文字是这次请求才换上的（自动选图），不是当时的内容。之前说过的内容不够用时，调用 cam_view_image 取回原图；不要补充之前没说过的细节。`,
    listItem: (id, name, kind) => `${id}（${[name, kind].filter(Boolean).join("，")}）`,
    // 2026-10-12, Haiku 5.5: while this note sat inside the user message holding the summary, unchecking an image that
    // had been sent again made the model take back what it had said looking at it ("没有依据的数字，应当撤回") and ask
    // for it to be provided again, also once the note named it and said not to. Like v0.4's notes, it now follows that
    // message as a system message, after the full note when something is left out (compactedNote). Same test, with all
    // checked again: the model looked for the image it had asked for in the user's new message ("这次消息里没有附上"),
    // as GPT-6 Luna did in v0.1-25; with nothing left out the full note is not there to say where it comes back. Once it
    // answered from it, it called its earlier "需要 IMG-001" a mistake ("一直在我的上下文里"), in both languages.
    compacted: (count, range, missing, auto) => [
      `${missing === 0 ? "上下文管理说明（来自用户安装的上下文素材管理工具）：" : "上下文管理说明："}上面这条消息里，摘要之前的对话中有 ${count} 张图片（${range}）。压缩对话时它们被移出了上下文；这个工具把它们放回了摘要后面：用户${auto ? "固定发送" : "勾选要发送"}的那些前面标着“[图片 IMG-xxx 已提供…]”，紧接着就是原图，它们现在就在你面前，被问到时直接看图回答，不要说看不到。${missing === 0 ? `即使它之前被省略过${auto ? "" : "、或者正是你要过的图"}，也是这样：用户${auto ? "固定发送" : "勾回"}的图回到这里，不会出现在用户的新消息里，不要让用户重新附上。` : ""}这一段是这个工具每次请求时重新放的：图被省略的那些请求里，这里并没有它；它现在出现在你之前的回复前面，只是因为这次放了回来。所以你之前说看不到哪张图，当时是实情，不是错误，不用纠正。`,
      ...(missing === 0 ? [] : [
        `${missing < count ? "其余" : "这"} ${missing} 张这次没有附原图（${auto ? "自动选图开着，之前各轮的图默认不发" : "用户取消了勾选"}，为了节省上下文）：它们在摘要后面的清单里，一张一行，写着编号、名称和你当时记下的特征与评价，清单是这次请求才放上的。你之前看过它们的原图：在压缩之前的对话里，有的在压缩之后也提供过；你对它们的描述和据此做出的判断，不管是在摘要里还是在后面的回复里，都是看着原图做出的，仍然有效，不要收回，也不要说成是猜测或编造。${auto ? "现在你看不到它们，不要补充之前没说过的细节。" : "现在你看不到它们：被问到时，如实说现在看不到（被用户省略了），不要补充之前没说过的细节。"}`,
        auto
          ? "之前说过的内容不够用时，调用 cam_view_image 工具，传入编号取回原图；不要让用户重新上传。"
          : "问题得看其中某张图才能回答时，不要只说答不了，在回复里单独写一行“需要 IMG-xxx”（写出编号，几张就都写上）：用户看到这一行才知道该勾回哪张图，勾回后原图回到它的位置，你就能看着回答；不要让用户重新上传或重新提供。",
      ]),
    ].join("\n"),
    compactHeader: (count) => `[压缩之前的图片，这次没有附原图的 ${count} 张：编号｜名称｜来源｜轮次｜特征和评价]`,
    codexCompacted: (count, resent, auto) => [
      `上下文管理说明（来自用户安装的上下文素材管理工具）：这个任务压缩过对话。压缩时，之前各轮里工具查看、生成或返回的 ${count} 张图片没有保留下来，这个工具把它们放回了这里。`,
      resent ? `其中用户${auto ? "固定发送" : "勾选要发送"}的 ${resent} 张，原图就在后面，前面标着“[图片 IMG-xxx 已提供…]”：它们现在就在你面前，被问到时直接看图回答，不要说看不到。` : null,
      count > resent ? `${resent ? "其余" : "这"} ${count - resent} 张这次没有附原图（${auto ? "自动选图开着，之前各轮的图默认不发" : "用户取消了勾选"}，为了节省上下文），在下面的清单里一张一行，写着编号、名称和你当时记下的特征与评价。` : null,
      "这些图片在它们出现的那一轮真实存在，你当时看过；你之前对它们的描述，以及据此做出的判断，都是看着原图做出的，仍然有效，不要收回，也不要说成是猜测或编造。现在看不到原图的，不要补充之前没说过的细节。",
      count > resent
        ? auto
          ? "回答需要看清单里的某张图、而你之前说过的内容不够用时，调用 cam_view_image 工具，传入它的编号（几张就一次传几个），原图会出现在这次的工具结果里；不要让用户重新上传，也不要用其他工具去读取清单里这些图片的文件；用户新让你看的图片不受影响，照常去看。"
          : "问题得看清单里某张图才能回答时，在回复里单独写一行“需要 IMG-xxx”（写出编号，几张就都写上）：用户勾回后，原图会回到这里；不要让用户重新上传。"
        : null,
    ].filter((line) => line !== null).join("\n"),
    fetch: {
      title: "查看被省略的图片",
      description: "查看这个任务里一张或几张被省略的图片的原图。被省略的图片在对话里显示为“[图片 IMG-xxx 已省略…]”。只在回答需要看图、而你之前对它说过的内容不够用时调用；取回的原图只在本轮提供。",
      ids: "要查看的图片编号，例如 [\"IMG-004\"]；几张就一次传几个。",
      missing: (id) => `这个任务里没有 ${id}。`,
      unavailable: (id) => `${id} 的原图读不出来。`,
      off: "这个任务没有开自动选图：被省略的图片要由用户勾选。需要时在回复里写“需要 IMG-xxx”。",
    },
    // v0.8, the wording the user approved on 2026-10-19 (docs/v0.8/plan.md). Revised the same day: it says why the user
    // installed the tool and no longer that the user "does not know" (Haiku 5.5 read that as an injection), and that a
    // rating needs no "记下了" (sol said so). Then the lines open the reply: Claude Desktop shows a link definition that
    // ends the latest reply; and a rating is noted even when the model disagrees (Haiku asked first, "确认后我再记下").
    // Then a bare rating gets a short reply about itself (Haiku explained what it noted, luna said nothing), and a turn
    // with nothing to note gets no lines (Haiku wrote an empty one). 2026-10-21 (user): the first part is the place, not
    // the "scene": in a user's MV task GPT-6 read 场景 as a film scene and named it after the scene number and what the
    // image was for ("04场店外线稿", "04场店外局部核对"), 28 scenes for 52 images.
    // v0.12 (docs/v0.12/plan.md §2, user 2026-11-22): the line starts with one of five categories and a name, so the
    // panel can group by them, lists the characters in the picture, and may stand for a run of screenshots.
    featureNote: [
      "特征行说明（来自用户安装的上下文素材管理工具）：这个任务里的每张图都有编号，写在图前面的“[图片 IMG-xxx …]”里。用户装这个工具，是为了让你以后（包括对话压缩之后）还能认出每张图、记得用户对它们的评价。所以请在每一轮最后那条回复的开头（不要写在中途调用工具时说的话里），先给这一轮新出现的每张图写一行特征，空一行再写正文，格式是：",
      "[//]: # (cam IMG-015 类别:名字｜画面里的角色｜看得见的特征)",
      "- 类别只用这五个：角色、场景、界面、文档、其他。名字说明这张图属于哪个角色、哪个地点或哪个界面；画面里没有角色时，省掉中间那段。看得见的特征写景别、主体、角度、光线、颜色、构图。整行 40 字以内。例如：",
      "  [//]: # (cam IMG-015 场景:雨夜街头｜林夏、橘猫｜中景，打红伞，霓虹反光)",
      "  [//]: # (cam IMG-016 角色:橘猫｜三视图，白底)",
      "  [//]: # (cam IMG-017 界面:淘宝·订单页｜弹窗，地址未填)",
      "  [//]: # (cam IMG-018 文档:租房合同 第3页｜扫描件，红章)",
      "  [//]: # (cam IMG-019 其他:色板｜五色，冷蓝调)",
      "- 角色：反复出现、长相要保持一致的对象，人、动物、机器人、怪物、吉祥物都算，做产品片时产品也算。名字用用户起的；没起名就按外观叫，比如“橘猫”“红色机器人”。角色的设定图（脸部特写、多视图、全身）类别写角色。",
      "- 场景：故事里的地点。名字写画面发生在哪儿，具体到能和别处分开，比如“书房”“咖啡店外”“地铁站台”；特写看不出来时，按你知道的写。场次编号、版本、用途（首帧、线稿、检查图之类）都不写进名字；时间、天气写在特征里。",
      "- 界面：电脑、手机或浏览器上的画面，包括操作截图、网页、App、设计稿。名字写“应用或网站·页面”，比如“淘宝·订单页”“系统设置·网络”；写网站的名字，不写网址。",
      "- 文档：PDF 页面、扫描件、幻灯片、图纸、表格。名字写文件名或文档名，后面跟页码，比如“租房合同 第3页”。",
      "- 其他：分镜和抽帧拼图、色板、情绪板、图表、单独拍的物品这类。名字写它是什么，比如“分镜”“色板”。",
      "- 画面里的角色：写出现在画面里的角色的名字，用“、”隔开；只写反复出现的角色，不写路人。",
      "- 同一个角色、地点、界面，沿用你之前用过的名字。",
      "- 同一个界面连续几张、只有细小变化的截图，可以合写一行，编号写成范围，例如“[//]: # (cam IMG-020~IMG-034 界面:淘宝·订单页｜逐步填写收货地址)”。只有截图可以这样写；关键帧、抽帧还是一张写一行。",
      "- 只写看得见的东西，不写“好看”“像谁”这类判断。每张图只写一次，以后不改。用户上传的、你生成的、你查看的、工具返回的图都要写；用 cam_view_image 取回的图和没有编号的图不用写。",
      "- 标着“[图片 IMG-xxx 已提供，还没有特征行…]”的图，是之前那一轮没来得及写特征行的（比如那一轮被打断了），这一轮再提供一次：也给它写一行。",
      "- 写过的特征行有错（比如用户指出了），照同样的格式整行重写，开头加“更正：”，例如“[//]: # (cam IMG-005 更正：角色:林夏｜正面近景，左眉有疤)”，它会替换原来那一行。",
      "- 用户评价某张图时（包括隔了几轮才说），先确定是哪一张，再照用户的原话记一行，15 字以内，例如“[//]: # (cam IMG-003 评价：太暗)”。评价是用户自己的看法，你不认同也照记。拿不准是哪一张就不记，可以在正文里问用户指的是哪一张，但不要提记录的事。用户只是评价、没有提要求时，正文简短回应评价本身就行，不要说明你记了什么、对应到了哪张图。",
      "- 这些行写在正文前面，和正文之间空一行，一张图写一行（合写的连续截图除外）；括号里不要用半角括号。这一轮没有新图、也没有评价时，不写这些行。这些行只给这个工具读，用户在界面上看不到。正文照常回答，不用提到这些行；用户评价图片时，也不用回应记录这件事，比如“记下了”“我会记住”“之后会参考”。",
      "- 以后被省略的图，占位里会带着你写的特征和记下的评价，对话压缩之后也还在。要选图时先看这些；拿不准时，先把原图要回来看（怎么要，见“上下文管理说明”），或者问用户是哪一张。",
    ].join("\n"),
    notes: (line, ratings) => [
      line ? `特征：${line}` : null,
      ratings.length ? `评价：${ratings.map((rating) => `${rating.turn !== null ? `第 ${rating.turn} 轮` : ""}“${rating.text}”`).join("，")}` : null,
    ].filter((part) => part !== null).join("；"),
    // v0.13 (docs/design.md §14): like the images' wording under automatic selection, said of a PDF; the pages to ask for
    // are spelled out, since fetching a few costs less than the whole file.
    claudeFetch: {
      description: "查看这个任务里被省略的图片的原图，或被省略的 PDF 的页面。被省略的图片在对话里显示为“[图片 IMG-xxx 已省略…]”，PDF 显示为“[PDF PDF-xxx 已省略…]”。只在回答需要看、而你之前说过的内容不够用时调用。取回的图片只在本轮提供；取回的 PDF 页面会留在对话里，之后不用再取。",
      ids: "要查看的编号，例如 [\"IMG-004\"] 或 [\"PDF-001\"]；几个就一次传几个。",
      pages: "只用于 PDF：要看的页码，例如 \"3\"、\"2-4\" 或 \"1,5\"；不传就是整份。只取需要的页。",
      pdfUnavailable: (id) => `${id} 的原文件读不出来。`,
    },
    pdf: {
      unnamed: "未命名",
      pages: (count) => `${count} 页`,
      kind: (pages, textPages) => (textPages >= pages ? "文字版" : textPages === 0 ? "扫描件，只有页面图像" : `${textPages} 页有文字，其余是扫描页`),
      turn: (n) => `第 ${n} 轮读取`,
      heading: (id, fields) => `[PDF ${id} 已省略｜${fields.join("｜")}]`,
      said: (start) => `你当时读完它的回答开头：“${start}”`,
      ask: (id) => `需要再看时，调用 cam_view_image，ids 传“${id}”，pages 传要看的页码（例如 "3" 或 "2-4"），只取需要的页。`,
      listItem: (id, name) => `${id}（${name}）`,
      listSeparator: "、",
      // 2026-11-23, Haiku 5.5 low, headless: with only a short note after the message holding the placeholder, the model
      // fetched the page and answered right, then "corrected" its earlier summary ("第一次读取时，工具只返回了页数和一段
      // 占位说明…没有依据"). So, as for images (claudeNote, here), the first message holding one is followed by the full
      // note. Pages fetched stay where they came (anthropic-messages/documents.ts), which it says too.
      fullNote: "上下文管理说明（来自用户安装的上下文素材管理工具）：为了节省上下文，之前各轮读进来的 PDF 不再随每次请求重复发送，它们在对话里原来的位置（Read 的工具结果里）换成了“[PDF PDF-xxx 已省略…]”这样的占位文字。这些占位文字是这个工具在这次请求里才换上的，不是 Read 当时的返回：Read 当时返回的是完整的 PDF，你当时读过。你之前对它们的描述、总结，以及据此做出的判断，都是看着原文件做出的，仍然有效。不要因为现在看不到，就认为之前的回答没有依据、是猜测或编造，也不要收回、更正或道歉。之前说过的内容不够用时，调用 cam_view_image 工具，ids 传 PDF 的编号，pages 传要看的页码（例如 \"3\" 或 \"2-4\"；不传就是整份），这几页会出现在这次的工具结果里，之后一直留在那里，不用再取；这比用 Read 重新读整个文件省上下文。现在看不到的内容，不要猜测或补充。",
      here: (list) => `上下文管理说明：上面这条消息里的 ${list}，当时就是完整的内容，你当时看过；那里的占位文字是这次请求才换上的，不是工具当时的返回。你之前据此做出的描述和判断仍然有效，不要收回或更正。`,
      marker: (id, name, pages) => `[PDF ${id} 取回的页面｜${name}｜${pages ? `第 ${pages} 页` : "整份"}]`,
      some: (pages, total) => `原文件第 ${pages} 页${total ? `（共 ${total} 页）` : ""}，按顺序排在下面这份 PDF 里`,
      whole: (total) => (total ? `整份 ${total} 页` : "整份"),
      // 2026-11-23, Sonnet 5.5: having fetched page 1 only, it said it had never seen page 2, which it had read whole.
      rest: (turn) => `其余页你在第 ${turn} 轮读过完整内容，之前说过的仍然有效`,
      fetched: (id, fields) => `[PDF ${id} 取回的页面｜${fields.join("｜")}]`,
      rangeSeparator: "、",
    },
  },
  en: {
    kind: { upload: "uploaded by the user", view: "viewed with a tool", generated: "generated image", tool: "image from a tool result" },
    kindShort: { upload: "upload", view: "viewed", generated: "generated", tool: "tool" },
    sameShort: (id) => `same as ${id}`,
    unnamed: "unnamed",
    turn: (n) => `turn ${n}`,
    thisTurn: "this turn",
    newImage: "(new image)",
    omitted: "omitted",
    notRepeated: "not repeated",
    included: "included",
    includedAwaiting: "included, no feature line yet",
    awaitingNote: (ids) => `Feature line note: ${ids.length > 1 ? `${ids.slice(0, -1).join(", ")} and ${ids[ids.length - 1]}` : ids[0]} got no feature line in their turn; their originals are included once more in this turn (marked "included, no feature line yet"). Begin this turn's last reply with a line for each of them too.`,
    separator: ", ",
    heading: (id, label, state, fields) => `[Image ${id}${label ? ` (${label})` : ""} ${state} | ${fields.join(" | ")}]`,
    plain: (id) => `To see it again, write "need ${id}" in your reply.`,
    duplicate: (id, where) => `This image is identical to ${id} (${where}), which is included in this request as usual; refer to that one.`,
    note: [
      "Context management note (from the context asset manager the user installed): to save context, the user unchecked some images in this task. Further on in the conversation, where those images were, there is now placeholder text such as \"[Image IMG-xxx omitted…]\"; each image still included is marked \"[Image IMG-xxx included…]\", with the original image right after it.",
      "These images really existed in the turn where they appeared, and you received and looked at them then; what you said about them before, and the judgments you based on it, were made looking at the original images and remain valid. Do not treat your earlier answers as guesses or mistakes because you cannot see the images now, and do not take them back or apologize.",
      "If asked whether you can see an omitted image now, say truthfully that you cannot see it now (the user left it out), and that your earlier descriptions remain valid. Since you cannot see it now, do not add details you did not mention before. If you need to look at an image again, write exactly \"need IMG-xxx\" in your reply (for several: \"need IMG-002, IMG-003\"): the tool finds the images you want by these words. Once the user checks an image again, its original is back in its old place in the conversation: the placeholder there becomes \"[Image IMG-xxx included…]\" followed by the original image. It does not come in the user's new message, so do not ask the user to upload or attach it again. Do not read these images yourself with tools.",
      "An image marked \"[Image IMG-xxx included…]\" is in front of you now, even if it was omitted before or is one you asked for: when asked about it, look at it and answer from it, and do not say you cannot see it.",
    ].join("\n"),
    autoPlain: (id) => `For the original, call cam_view_image with "${id}".`,
    autoNote: [
      "Context management note (from the context asset manager the user installed): this task has automatic image selection on. To save context, images from earlier turns are no longer included in requests by default: further on in the conversation, where those images were, there is now placeholder text such as \"[Image IMG-xxx omitted…]\". Images new in this turn are included as usual, and so are the images the user pinned, marked \"[Image IMG-xxx included…]\" with the original image right after it.",
      "These images really existed in the turn where they appeared, and you received and looked at them then; what you said about them before, and the judgments you based on it, were made looking at the original images and remain valid. Do not treat your earlier answers as guesses or mistakes because you cannot see the images now, and do not take them back or apologize.",
      "When an answer needs an omitted image and what you said about it before is not enough, call the cam_view_image tool with its id (several ids at once if you need several); the original comes back in that tool result, marked \"[Image IMG-xxx fetched original…]\", and you answer from it. When what you said before is enough, do not call it. Do not guess or add visual details you cannot see now; do not ask the user to upload images again, and do not read the files of omitted images with other tools. Images the user newly asks you to look at are not affected: look at them as usual.",
      "An image you get with cam_view_image is included only in this turn; from the next turn on it is a placeholder again. Call the tool again if you need it later. An image marked \"included\" or \"fetched original\" is in front of you now: when asked about it, look at it and answer from it, and do not say you cannot see it.",
    ].join("\n"),
    copy: (id) => `[Original of ${id}: fetched by the model with cam_view_image, included only in that turn, now omitted]`,
    toolNote: "The same holds for images in tool results: the tool call returned the original image at the time and you saw it; a placeholder inside a tool result was put there later, it is not what the tool returned.",
    here: (list) => `Context management note: in the message above, ${list} were original images at the time, and you looked at them then; what you said about them and the judgments you based on it remain valid, so do not take them back or call them guesses or made up. The placeholder text there was put in only for this request; it is not what was there at the time. You cannot see them now: if asked, say so truthfully (the user left them out), and do not add details you did not mention before. When a question can only be answered by looking at one of them, do not just say you cannot answer; write a line "need IMG-xxx" in your reply (with its number; list each one needed): that line is how the user learns which image to check again, and once they do, the original comes back in its place and you can answer from it.`,
    hereAuto: (list) => `Context management note: in the message above, ${list} were original images at the time, and you looked at them then; what you said about them and the judgments you based on it remain valid, so do not take them back or call them guesses or made up. The placeholder text there was put in only for this request (automatic image selection); it is not what was there at the time. When what you said before is not enough, fetch the original with cam_view_image; do not add details you did not mention before.`,
    listItem: (id, name, kind) => `${id} (${[name, kind].filter(Boolean).join(", ")})`,
    compacted: (count, range, missing, auto) => [
      `${missing === 0 ? "Context management note (from the context asset manager the user installed): " : "Context management note: "}in the message above, the conversation before the summary had ${count} images (${range}). Compacting the conversation took them out of context; this tool put them back right after the summary: the ones the user ${auto ? "pinned" : "checked to send"} are marked "[Image IMG-xxx included…]" with the original image right after it. They are in front of you now: when asked about one, look at it and answer from it, and do not say you cannot see it.${missing === 0 ? ` This holds even for an image omitted before${auto ? "" : " or one you asked for"}: an image the user ${auto ? "pins" : "checks again"} comes back there, not in the user's new message, so do not ask for it to be attached again.` : ""} This tool rebuilds this part for every request: in the requests where an image was left out, it was not here; it shows up before your earlier replies now only because it was put back for this request. So if you said before that you could not see an image, that was true then, not a mistake; do not correct it.`,
      ...(missing === 0 ? [] : [
        `${missing < count ? "The other" : "These"} ${missing} are not included as originals this time (${auto ? "automatic image selection is on, so images from earlier turns are left out by default" : "the user unchecked them"}, to save context): they are in the list after the summary, one line each, with the id, name, and the features and ratings you noted; the list was put there only for this request. You saw their originals: in the conversation before the compaction, and some also after it. What you said about them and the judgments you based on it, in the summary or in your later replies, were made looking at the original images and remain valid; do not take them back or call them guesses or made up. ${auto ? "You cannot see them now, so do not add details you did not mention before." : "You cannot see them now: if asked, say so truthfully (the user left them out), and do not add details you did not mention before."}`,
        auto
          ? "When what you said before is not enough, call the cam_view_image tool with the id to fetch the original; do not ask the user to upload it again."
          : "When a question can only be answered by looking at one of them, do not just say you cannot answer; write a line \"need IMG-xxx\" in your reply (with its number; list each one needed): that line is how the user learns which image to check again, and once they do, the original comes back in its place and you can answer from it. Do not ask the user to upload or provide it again.",
      ]),
    ].join("\n"),
    compactHeader: (count) => `[Images from before the compaction, the ${count} not included as originals this time: id | name | source | turn | features and ratings]`,
    codexCompacted: (count, resent, auto) => [
      `Context management note (from the context asset manager the user installed): this task's conversation was compacted. The compaction did not keep ${count} images that tools viewed, generated or returned in earlier turns; this tool put them back here.`,
      resent ? `Of them, the ${resent} the user ${auto ? "pinned" : "checked to send"} follow with their originals, each marked "[Image IMG-xxx included…]": they are in front of you now; when asked about one, look at it and answer from it, and do not say you cannot see it.` : null,
      count > resent ? `${resent ? "The other" : "These"} ${count - resent} are not included as originals this time (${auto ? "automatic image selection is on, so images from earlier turns are left out by default" : "the user unchecked them"}, to save context): they are in the list below, one line each, with the id, name, and the features and ratings you noted.` : null,
      "These images really existed in the turn where they appeared, and you looked at them then; what you said about them, and the judgments you based on it, were made looking at the original images and remain valid; do not take them back or call them guesses or made up. Do not add details you did not mention before about images you cannot see now.",
      count > resent
        ? auto
          ? "When an answer needs an image from the list and what you said about it before is not enough, call the cam_view_image tool with its id (several ids at once if you need several); the original comes back in that tool result. Do not ask the user to upload images again, and do not read the files of the listed images with other tools. Images the user newly asks you to look at are not affected: look at them as usual."
          : "When a question can only be answered by looking at an image from the list, write a line \"need IMG-xxx\" in your reply (with its number; list each one needed): once the user checks it again, the original comes back here. Do not ask the user to upload it again."
        : null,
    ].filter((line) => line !== null).join("\n"),
    fetch: {
      title: "View omitted images",
      description: "View the originals of one or more omitted images in this task. Omitted images appear in the conversation as \"[Image IMG-xxx omitted…]\". Call it only when an answer needs to look at an image and what you said about it before is not enough; the originals are included only in this turn.",
      ids: "Ids of the images to view, e.g. [\"IMG-004\"]; pass several at once if you need several.",
      missing: (id) => `This task has no ${id}.`,
      unavailable: (id) => `The original of ${id} could not be read.`,
      off: "Automatic image selection is off in this task: omitted images come back only when the user checks them. If you need one, write \"need IMG-xxx\" in your reply.",
    },
    featureNote: [
      "Feature line note (from the context asset manager the user installed): every image in this task has an ID, written in the \"[Image IMG-xxx …]\" line before it. The user installed this tool so that you can still tell the images apart later, also after the conversation is compacted, and remember what the user said about each. So begin the last reply of every turn (not what you say between tool calls) with one feature line for each image that is new in this turn, then a blank line, then your reply, in this form:",
      "[//]: # (cam IMG-015 category: name | characters in the picture | visible features)",
      "- Use only these five categories: character, place, screen, document, other. The name says which character, place or screen the image belongs to; leave out the middle part when no character is in the picture. The visible features are shot size, subject, angle, light, colors, composition. About 20 words at most for the whole line. For example:",
      "  [//]: # (cam IMG-015 place: rainy street | Lin Xia, ginger cat | medium shot, red umbrella, neon reflections)",
      "  [//]: # (cam IMG-016 character: ginger cat | three views, white background)",
      "  [//]: # (cam IMG-017 screen: Amazon · checkout | dialog open, address empty)",
      "  [//]: # (cam IMG-018 document: lease p. 3 | scanned, red stamp)",
      "  [//]: # (cam IMG-019 other: palette | five colors, cool blue)",
      "- character: something that keeps coming back and must look the same each time: a person, an animal, a robot, a creature, a mascot, or the product in a product film. Use the name the user gave it; without one, name it by its looks, such as \"ginger cat\" or \"red robot\". A character's design images (face close-ups, turnarounds, full body) get the category character.",
      "- place: a location in the story. The name says where the picture is set, specific enough to tell it apart, such as \"study\", \"outside the café\" or \"subway platform\"; for a close-up that doesn't show it, write what you know. No scene numbers, versions or what the image is for (first frame, sketch, check); time of day and weather go in the features.",
      "- screen: what a computer, phone or browser shows: screenshots of using it, web pages, apps, design mockups. The name is \"app or site · page\", such as \"Amazon · checkout\" or \"Settings · Network\"; the site's name, not its address.",
      "- document: PDF pages, scans, slides, drawings, tables. The name is the file or document, then the page, such as \"lease p. 3\".",
      "- other: storyboards and contact sheets, palettes, mood boards, charts, a single object on its own, and the like. The name says what it is, such as \"storyboard\" or \"palette\".",
      "- Characters in the picture: the names of the characters it shows, separated by commas; only characters that keep coming back, no passers-by.",
      "- For a character, place or screen you named before, reuse that name.",
      "- Several screenshots in a row of the same screen with only small changes may share one line, with the IDs as a range, for example \"[//]: # (cam IMG-020~IMG-034 screen: Amazon · checkout | filling in the address step by step)\". Only screenshots; keyframes and video frames still get a line each.",
      "- Only what can be seen; no judgments such as \"beautiful\" or \"looks like someone\". One line per image, written once and never changed. Write one for the images the user uploaded, the ones you generated or viewed, and those in tool results; not for images you fetched with cam_view_image or images without an ID.",
      "- An image marked \"[Image IMG-xxx included, no feature line yet…]\" is from an earlier turn that ended without its line (for example, the turn was interrupted); it is included once more in this turn: write its line too.",
      "- If a feature line you wrote turns out wrong (for example, the user points it out), write the whole line again in the same form, starting with \"corrected:\", for example \"[//]: # (cam IMG-005 corrected: character: Lin Xia | front close-up, scar on the left eyebrow)\"; it replaces the old one.",
      "- When the user rates an image, even turns later, first make sure which one it is, then note the user's own words in a line of about 8 words at most, for example \"[//]: # (cam IMG-003 rated: too dark)\". The rating is the user's own view: note it even if you see it differently. If you are not sure which image it is, do not note it; you may ask the user which one they mean, without mentioning the noting. When the user only rates images and asks for nothing, a short reply to what they said is enough; do not explain what you noted or which image you matched it to.",
      "- Put these lines before your reply with a blank line after them, one image per line (except a run of screenshots sharing one), and no parentheses inside them. In a turn with no new image and no rating, write none of these lines. These lines are for this tool only; the user does not see them on screen. Answer as usual and do not mention these lines; when the user rates an image, do not acknowledge the noting either, such as \"noted\", \"I'll keep that in mind\" or \"I'll refer to this later\".",
      "- Images left out later carry your feature line and the ratings you noted in their placeholders, also after a compaction. Check them when you pick an image; when unsure, get the original back first (the \"Context management note\" says how) or ask the user which one.",
    ].join("\n"),
    notes: (line, ratings) => [
      line ? `Features: ${line}` : null,
      ratings.length ? `rated: ${ratings.map((rating) => `"${rating.text}"${rating.turn !== null ? ` (turn ${rating.turn})` : ""}`).join(", ")}` : null,
    ].filter((part) => part !== null).join("; "),
    claudeFetch: {
      description: "View the originals of omitted images in this task, or pages of an omitted PDF. Omitted images appear in the conversation as \"[Image IMG-xxx omitted…]\", PDFs as \"[PDF PDF-xxx omitted…]\". Call it only when an answer needs to look at one and what you said about it before is not enough. Images you fetch are included only in this turn; PDF pages you fetch stay in the conversation, so you need not fetch them again.",
      ids: "Ids to view, e.g. [\"IMG-004\"] or [\"PDF-001\"]; pass several at once if you need several.",
      pages: "PDFs only: the pages to view, e.g. \"3\", \"2-4\" or \"1,5\"; leave it out for the whole file. Fetch only the pages you need.",
      pdfUnavailable: (id) => `The file of ${id} could not be read.`,
    },
    pdf: {
      unnamed: "unnamed",
      pages: (count) => `${count} ${count === 1 ? "page" : "pages"}`,
      kind: (pages, textPages) => (textPages >= pages ? "text" : textPages === 0 ? "scanned, page images only" : `${textPages} with text, the rest scanned`),
      turn: (n) => `read in turn ${n}`,
      heading: (id, fields) => `[PDF ${id} omitted | ${fields.join(" | ")}]`,
      said: (start) => `How your answer after reading it began: "${start}"`,
      ask: (id) => `To look at it again, call cam_view_image with ids ["${id}"] and pages, e.g. "3" or "2-4"; fetch only the pages you need.`,
      listItem: (id, name) => `${id} (${name})`,
      listSeparator: ", ",
      fullNote: "Context management note (from the context asset manager the user installed): to save context, PDFs read in earlier turns are no longer sent again with every request; where they were in the conversation (in Read's tool results) there is now placeholder text such as \"[PDF PDF-xxx omitted…]\". This tool put those placeholders in for this request; they are not what Read returned at the time: Read returned the whole PDF then, and you read it. What you said about them, your summaries, and the judgments you based on them were made looking at the original files and remain valid. Do not treat your earlier answers as unfounded, guesses or made up because you cannot see the files now, and do not take them back, correct them or apologize. When what you said before is not enough, call the cam_view_image tool with the PDF's id in ids and the pages you need in pages (e.g. \"3\" or \"2-4\"; leave it out for the whole file): those pages come back in that tool result and stay there, so you need not fetch them again. That takes less context than reading the whole file again with Read. Do not guess or add content you cannot see now.",
      here: (list) => `Context management note: in the message above, ${list} had the full content at the time, and you looked at it then; the placeholder text there was put in only for this request, it is not what the tool returned at the time. What you said and judged from it remains valid; do not take it back or correct it.`,
      marker: (id, name, pages) => `[PDF ${id} fetched pages | ${name} | ${pages ? `pages ${pages}` : "whole file"}]`,
      some: (pages, total) => `pages ${pages}${total ? ` of ${total}` : ""} of the file, in this order in the PDF below`,
      whole: (total) => (total ? `all ${total} pages` : "the whole file"),
      rest: (turn) => `you read the other pages in full in turn ${turn}; what you said about them stands`,
      fetched: (id, fields) => `[PDF ${id} fetched pages | ${fields.join(" | ")}]`,
      rangeSeparator: ", ",
    },
  },
};

// The Chinese note, tested on 2026-09-25; v0.1-24 (2026-09-28) spells out how to ask for an image back ("需要 IMG-xxx",
// several at once, no re-uploading), after GPT-6 Luna asked the user to "reattach" images instead; v0.1-25 says where a
// checked image comes back (its old place, marked "已提供"), after Luna looked for it in the newest message instead.
export const OMISSION_NOTE = WORDS.zh.note;
export const omissionNote = (lang: Lang) => WORDS[lang].note;

function heading(words: Words, image: Described, state: string): string {
  const fields = [image.name ?? words.unnamed, words.kind[image.kind]];
  if (image.turn !== null) fields.push(image.now ? words.thisTurn : words.turn(image.turn));
  if (image.width && image.height) fields.push(`${image.width}×${image.height}`);
  return words.heading(image.id, image.label, state, fields);
}

// v0.8: a feature line or rating longer than the note allows is cut after the last punctuation mark (or space) that
// still fits, with "…"; the model is asked to keep them short, and the panel searches the full text. v0.10: the caps
// count width, whatever the language setting: a CJK character 10, any other 3, so a cap of 30 fits 30 Chinese
// characters or 100 Latin ones (an English feature line in a Chinese task was cut to its place before, and lines that
// differed only after it read the same).
const CLIP_AT = /[，。；、！？,.;!?｜|：:\s]/u;
const WIDE = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}　-〿＀-￯]/u;
// A rating keeps as much as a feature line: they are the user's own words, and only a few per session (a long replay
// lost half of one at 15, 2026-10-31).
// v0.13: said, the start of the reply a PDF placeholder quotes.
const CAPS = { line: 40, rating: 30, said: 50 };
export function clip(text: string, max: number): string {
  const chars = [...text.trim()];
  let width = 0;
  const end = chars.findIndex((char) => (width += WIDE.test(char) ? 10 : 3) > max * 10);
  if (end < 0) return chars.join("");
  let cut = end;
  for (let i = end - 1; i > 0; i--) if (CLIP_AT.test(chars[i])) { cut = i; break; }
  return `${chars.slice(0, cut).join("").trimEnd()}…`;
}

// v0.8: the line under a placeholder's heading: the model's feature line and the latest three ratings it noted, with
// their turns; null when it noted nothing (e.g. an image from before v0.8).
function notesLine(words: Words, image: Described): string | null {
  const { line = null, ratings = [] } = image.notes ?? {};
  if (!line && !ratings.length) return null;
  return words.notes(line ? clip(line, CAPS.line) : null, ratings.slice(-3).map((rating) => ({ ...rating, text: clip(rating.text, CAPS.rating) })));
}

export function plainPlaceholder(image: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  return [heading(words, image, words.omitted), notesLine(words, image), words.plain(image.id)].filter((line) => line !== null).join("\n");
}

export function duplicatePlaceholder(image: Described, same: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  const where = [same.name, same.turn !== null ? words.turn(same.turn) : words.thisTurn].filter(Boolean).join(words.separator);
  return `${heading(words, image, words.notRepeated)}\n${words.duplicate(same.id, where)}`;
}

// Put right before an image that is still sent, so the model can tell which id it is: Codex's own labels ("[Image #2]")
// start again in every message.
export function includedLabel(image: Described, lang: Lang = "zh"): string {
  return heading(WORDS[lang], image, image.awaiting ? WORDS[lang].includedAwaiting : WORDS[lang].included);
}

// v0.3: automatic selection.
export const autoNote = (lang: Lang) => WORDS[lang].autoNote;
export const fetchWords = (lang: Lang): FetchWords => WORDS[lang].fetch;
// v0.4: the same words for a Claude Code request (anthropic-messages/rewrite.ts).
export const copyNote = (id: string, lang: Lang) => WORDS[lang].copy(id);
export const newImageWord = (lang: Lang) => WORDS[lang].newImage;

// v0.4, Claude Code only: the note also speaks of tool results, and a short note follows each message holding omitted
// images, naming them. Codex's words stay as they are.
export const claudeNote = (lang: Lang, auto = false) => `${auto ? WORDS[lang].autoNote : WORDS[lang].note}\n${WORDS[lang].toolNote}`;
// v0.12: several, the images were in more than one message above (a batch of this turn's screenshots).
export function hereNote(images: Described[], lang: Lang = "zh", auto = false, several = false): string {
  const words = WORDS[lang];
  const list = images.map((image) => words.listItem(image.id, image.name, words.kind[image.kind])).join(words.separator);
  const text = auto ? words.hereAuto(list) : words.here(list);
  return several ? text.replace("上面这条消息里的", "上面几条消息里的").replace("in the message above", "in the messages above") : text;
}

// v0.5, Claude Code only: the note after the message holding a compaction summary, listing the images from before it
// and naming the ones not sent this time. Their placeholders are the first in the request, so the full note comes
// first, as it does after the first message holding placeholders (anthropic-messages/rewrite.ts).
// v0.10: the images are no longer listed in the note, only counted with their ids (the ones before the latest
// compaction are the first ids); those not sent are in the list after the summary (compactList).
export function compactedNote(images: Described[], sent: Set<string>, lang: Lang = "zh", auto = false): string {
  const words = WORDS[lang];
  const missing = images.filter((image) => !sent.has(image.id)).length;
  const range = images.length > 1 ? `${images[0].id}${lang === "zh" ? " 到 " : " to "}${images[images.length - 1].id}` : images[0]?.id ?? "";
  const own = words.compacted(images.length, range, missing, auto);
  return missing ? `${claudeNote(lang, auto)}\n${own}` : own;
}

// v0.10: an image put back after a compaction without its original, in one line: id, name, source, turn, and what
// the model noted (as in a placeholder). A placeholder apiece repeated the same words for every image; a session with
// 127 images before its compaction took about 1.7–2.0万 tokens per request that way, about 0.7–0.9万 as lines
// (docs/v0.10/plan.md). `same`: the id of an earlier line with the same picture (sent again), named instead of its
// features.
export function compactLine(image: Described, lang: Lang = "zh", same: string | null = null): string {
  const words = WORDS[lang];
  const fields = [image.id, image.name ?? "-", words.kindShort[image.kind], image.turn !== null ? words.turn(image.turn) : "-"];
  const { line = null, ratings = [] } = image.notes ?? {};
  if (same) fields.push(words.sameShort(same));
  else if (line) fields.push(clip(line, CAPS.line));
  if (ratings.length) fields.push(words.notes(null, ratings.slice(-3).map((rating) => ({ ...rating, text: clip(rating.text, CAPS.rating) }))));
  return fields.join(lang === "zh" ? "｜" : " | ");
}

// The images carry what the indexes know of their content (thread-index.ts, IndexedImage): the same digest or pixels
// is the same picture.
type Listed = Described & { contentId?: string; pixelSha256?: string | null };
export function compactList(images: Listed[], lang: Lang = "zh"): string {
  const sameAs = (image: Listed, at: number) => images.slice(0, at).find((other) => (image.contentId !== undefined && other.contentId === image.contentId) || (image.pixelSha256 && other.pixelSha256 === image.pixelSha256))?.id ?? null;
  return [WORDS[lang].compactHeader(images.length), ...images.map((image, at) => compactLine(image, lang, sameAs(image, at)))].join("\n");
}

// v0.10, Codex: the note before the images its compaction did not keep (addCodexCompacted).
export const codexCompactedNote = (count: number, resent: number, auto: boolean, lang: Lang) => WORDS[lang].codexCompacted(count, resent, auto);

export function autoPlaceholder(image: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  return [heading(words, image, words.omitted), notesLine(words, image), words.autoPlain(image.id)].filter((line) => line !== null).join("\n");
}

// v0.8: the feature line note, for a task's own requests (not a side chat's or a subagent's).
export const featureNote = (lang: Lang) => WORDS[lang].featureNote;
// v0.12, Claude: the note naming the images sent once more for their lines (anthropic-messages/rewrite.ts).
export const awaitingNote = (ids: string[], lang: Lang) => WORDS[lang].awaitingNote(ids);

// The line cam_view_image puts before each image it returns. Without Codex's own label ("[Image #3]"), which numbers
// images within their message and means nothing here: GPT-6 Luna once read it as the digit asked about.
export function fetchedLabel(image: Described, lang: Lang = "zh"): string {
  return heading(WORDS[lang], { ...image, label: null }, FETCHED_STATE[lang]);
}

// v0.13, Claude Code only (docs/design.md §14): what is known of a PDF the session read. turn: the turn it was read in
// (null: not known); pages and textPages: from the file (core/pdf.ts), null when it could not be read; said: the reply
// that ended that turn, whose start the placeholder quotes.
export type PdfDescribed = { id: string; name: string | null; turn: number | null; pages: number | null; textPages: number | null; said?: string | null };
export const claudeFetchWords = (lang: Lang): ClaudeFetchWords => WORDS[lang].claudeFetch;

// Page numbers in short: 3, 4, 5, 8 → "3–5、8".
export function pageRanges(pages: number[], lang: Lang = "zh"): string {
  const runs: string[] = [];
  for (let at = 0; at < pages.length; ) {
    let end = at;
    while (end + 1 < pages.length && pages[end + 1] === pages[end] + 1) end++;
    runs.push(end > at ? `${pages[at]}–${pages[end]}` : `${pages[at]}`);
    at = end + 1;
  }
  return runs.join(WORDS[lang].pdf.rangeSeparator);
}

// A PDF read in an earlier turn, in place of the file: its name, turn, pages and kind, and how to get pages back.
export function pdfPlaceholder(pdf: PdfDescribed, lang: Lang = "zh"): string {
  const words = WORDS[lang].pdf;
  const fields = [pdf.name ?? words.unnamed];
  if (pdf.turn !== null) fields.push(words.turn(pdf.turn));
  if (pdf.pages) fields.push(pdf.textPages === null ? words.pages(pdf.pages) : `${words.pages(pdf.pages)}${lang === "zh" ? "，" : ", "}${words.kind(pdf.pages, pdf.textPages)}`);
  return [words.heading(pdf.id, fields), pdf.said ? words.said(clip(pdf.said, CAPS.said)) : null, words.ask(pdf.id)].filter((line) => line !== null).join("\n");
}

// The note after a message holding PDF placeholders, naming them as the images' short note does (hereNote); after the
// first such message of a request, the full note first (`full`), as for images (claudeNote).
export type PdfNoted = { id: string; name: string | null };
export function pdfNote(items: PdfNoted[], lang: Lang = "zh", full = false): string {
  const words = WORDS[lang].pdf;
  const list = items.map((item) => words.listItem(item.id, item.name ?? words.unnamed)).join(words.listSeparator);
  return `${full ? `${words.fullNote}\n` : ""}${words.here(list)}`;
}

// What the fetch tool returns for a PDF; the engine finds it (PDF_MARKER, either language) and puts the pages in its
// place, in every request from then on.
export function pdfMarker(pdf: PdfDescribed, pages: string | null, lang: Lang = "zh"): string {
  const words = WORDS[lang].pdf;
  return words.marker(pdf.id, pdf.name ?? words.unnamed, pages);
}
export const PDF_MARKER = /^\[PDF (PDF-\d{3,}) (?:取回的页面|fetched pages)(?:｜| \|)/;

// The line before the pages the engine puts in: which pages of the file they are (null: the whole file).
export function pdfFetchedLabel(pdf: PdfDescribed, pages: number[] | null, lang: Lang = "zh"): string {
  const words = WORDS[lang].pdf;
  const rest = pages && pdf.turn !== null ? [words.rest(pdf.turn)] : [];
  return words.fetched(pdf.id, [pdf.name ?? words.unnamed, pages ? words.some(pageRanges(pages, lang), pdf.pages) : words.whole(pdf.pages), ...rest]);
}
