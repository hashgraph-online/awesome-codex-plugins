# Xquik TypeScript Types: Support

```typescript
type SupportTicketStatus = "open" | "in_progress" | "resolved" | "closed";
type SupportAttachmentStatus = "pending" | "ready" | "failed";

interface SupportAttachmentReceipt {
  publicId: string;
  status: SupportAttachmentStatus;
}

interface SupportAttachment extends SupportAttachmentReceipt {
  filename: string;
  contentType: "image/jpeg" | "image/png" | "image/gif" | "image/webp"
    | "video/mp4" | "video/quicktime" | "video/webm";
  kind: "image" | "video";
  sizeBytes: number;
  url: string;
}

interface SupportMessage {
  body: string;
  sender: "user" | "support" | "system";
  createdAt: string;
  attachments: SupportAttachment[];
}

interface SupportTicket {
  publicId: string;
  subject: string;
  status: SupportTicketStatus;
  createdAt: string;
  updatedAt: string;
  messageCount?: number;
  messages?: SupportMessage[];
}

interface SupportMutationResponse {
  publicId: string;
  attachments: SupportAttachmentReceipt[];
}

type SupportContent = { body: string } | { body?: string; attachments: Blob[] };
type CreateTicketRequest = SupportContent & { subject: string };
type ReplyToTicketRequest = SupportContent;
```
