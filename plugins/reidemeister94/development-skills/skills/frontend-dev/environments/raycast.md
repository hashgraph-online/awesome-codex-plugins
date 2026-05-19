# Raycast Extension Patterns

Environment overlay for Raycast extensions. Used alongside [react.md](../patterns/react.md). Referenced by the frontend-dev skill when `@raycast/api` is detected in dependencies.

---

## Review Standards (Additional)

- Raycast API components used correctly (List, Detail, Form, Action, ActionPanel)
- Preferences system used for user configuration (not env vars or dotenv)
- Navigation via `push`/`pop` (not React Router)
- Toast notifications for async feedback
- Proper loading states via `isLoading` prop
- Icons from `@raycast/api` Icon enum
- No HTML or CSS — Raycast renders natively

---

## Architecture

```
src/
├── index.tsx               # Main command entry point
├── search.tsx              # Additional command
├── components/             # Reusable components
├── hooks/                  # Custom hooks
├── lib/                    # Utilities and API clients
├── types.ts                # Shared types
└── package.json            # Raycast metadata + dependencies
```

**Key concept:** Each `.tsx` file in `src/` listed in `package.json` commands is a separate Raycast command entry point.

---

## Core Components

### List View

```tsx
import { List, ActionPanel, Action, Icon } from "@raycast/api";
import { useState } from "react";

export default function SearchItems() {
  const [items, setItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // ... fetch items

  return (
    <List isLoading={isLoading} searchBarPlaceholder="Search items...">
      {items.map(item => (
        <List.Item
          key={item.id}
          title={item.name}
          subtitle={item.description}
          icon={Icon.Document}
          accessories={[{ text: item.date }]}
          actions={
            <ActionPanel>
              <Action.Push title="View Details" target={<ItemDetail item={item} />} />
              <Action.OpenInBrowser url={item.url} />
              <Action.CopyToClipboard content={item.name} />
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
```

### Detail View

```tsx
import { Detail, ActionPanel, Action } from "@raycast/api";

function ItemDetail({ item }: { item: Item }) {
  const markdown = `# ${item.name}\n\n${item.description}`;

  return (
    <Detail
      markdown={markdown}
      metadata={
        <Detail.Metadata>
          <Detail.Metadata.Label title="Status" text={item.status} />
          <Detail.Metadata.Link title="URL" target={item.url} text="Open" />
          <Detail.Metadata.Separator />
          <Detail.Metadata.TagList title="Tags">
            {item.tags.map(tag => (
              <Detail.Metadata.TagList.Item key={tag} text={tag} />
            ))}
          </Detail.Metadata.TagList>
        </Detail.Metadata>
      }
      actions={
        <ActionPanel>
          <Action.OpenInBrowser url={item.url} />
        </ActionPanel>
      }
    />
  );
}
```

### Form

```tsx
import { Form, ActionPanel, Action, showToast, Toast } from "@raycast/api";

export default function CreateItem() {
  async function handleSubmit(values: { name: string; description: string }) {
    try {
      await api.createItem(values);
      showToast({ style: Toast.Style.Success, title: "Item created" });
    } catch (error) {
      showToast({ style: Toast.Style.Failure, title: "Failed to create item" });
    }
  }

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Create Item" onSubmit={handleSubmit} />
        </ActionPanel>
      }
    >
      <Form.TextField id="name" title="Name" placeholder="Item name" />
      <Form.TextArea id="description" title="Description" />
      <Form.Dropdown id="priority" title="Priority">
        <Form.Dropdown.Item value="low" title="Low" />
        <Form.Dropdown.Item value="medium" title="Medium" />
        <Form.Dropdown.Item value="high" title="High" />
      </Form.Dropdown>
    </Form>
  );
}
```

---

## Preferences

```tsx
import { getPreferenceValues } from "@raycast/api";

interface Preferences {
  apiKey: string;
  baseUrl: string;
  defaultView: "list" | "grid";
}

const preferences = getPreferenceValues<Preferences>();
```

Define in `package.json`:
```json
{
  "preferences": [
    {
      "name": "apiKey",
      "type": "password",
      "required": true,
      "title": "API Key",
      "description": "Your API key"
    }
  ]
}
```

---

## Async Patterns

```tsx
import { showToast, Toast } from "@raycast/api";
import { useFetch } from "@raycast/utils";

// Built-in hook for data fetching
function SearchItems() {
  const { data, isLoading, error } = useFetch<Item[]>("https://api.example.com/items");

  if (error) {
    showToast({ style: Toast.Style.Failure, title: "Failed to load items" });
  }

  return <List isLoading={isLoading}>...</List>;
}
```

---

## Verification

- Build: `ray build`
- Lint: `eslint`
- Test: limited — Raycast has no built-in test runner. Use `vitest` if configured.
- Manual testing: `ray develop` for live reload

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| HTML/CSS markup | Raycast native components (List, Detail, Form) |
| React Router | `Action.Push` / `Action.Pop` for navigation |
| `dotenv` for config | Raycast Preferences system |
| `console.log` for feedback | `showToast()` |
| Custom spinners | `isLoading` prop on List/Detail/Form |
