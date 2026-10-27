# Text formatters & rich text

Angular's formatter surface is richer than React's and has five dedicated guides.

## Built-in formatters
`CometChatTextFormatter` (base) · `CometChatMentionsFormatter` · `CometChatUrlFormatter` · `CometChatEmojiFormatter` · `CometChatMarkdownFormatter`

Mentions and URLs are **on by default**. Do not add them.

## Applying formatters to a list
Both `<cometchat-message-list>` and `<cometchat-conversations>` accept a `textFormatters` input:
```html
<cometchat-message-list [user]="activeUser()" [textFormatters]="formatters"></cometchat-message-list>
```
```ts
import { CometChatMentionsFormatter, CometChatUrlFormatter } from '@cometchat/chat-uikit-angular';
readonly formatters = [new CometChatMentionsFormatter(), new CometChatUrlFormatter()];
```
Passing `textFormatters` **replaces** the defaults for that component — include the ones you still want.

## App-wide defaults
`FormatterConfigService` sets formatters once for every text-rendering component instead of per-component. Prefer it when the same set applies everywhere.

## Custom formatter
Extend `CometChatTextFormatter`. Fetch `{DOCS_BASE}/ui-kit/angular/guides/custom-text-formatter.md` for the exact hook signatures before implementing — the guides for hashtag, shortcut, mentions and URL formatters each show a working variant.

## Rich text editing
The composer's rich text editor (bold, italic, lists, code, links, undo/redo) is backed by `RichTextEditorService` and uses native browser APIs — no external editor dependency. Guide: `{DOCS_BASE}/ui-kit/angular/guides/rich-text-formatting.md`. Do not bolt on a third-party editor; it will fight the composer's own state.
