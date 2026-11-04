# Deliverability Requirements (checked October 2026)

A lifecycle sequence only works if it reaches the inbox. These are the mailbox
provider rules that decide that, with primary sources. Verify the linked pages
before launch; providers update them without notice.

## Gmail

Source: Google, Email sender guidelines FAQ,
https://support.google.com/mail/answer/14229414

- **Bulk sender:** close to 5,000 or more messages to personal Gmail accounts
  in 24 hours, counted across the primary domain. The status does not expire.
- **All senders:** SPF or DKIM, valid forward and reverse DNS, TLS, and a spam
  rate kept low.
- **Bulk senders:** SPF **and** DKIM; a DMARC record (p=none minimum) with the
  From domain aligned to SPF or DKIM.
- **Unsubscribe:** marketing and promotional mail needs one-click unsubscribe
  through RFC 8058 `List-Unsubscribe` and `List-Unsubscribe-Post` headers, plus
  a visible link in the body. Honor requests within 48 hours. Transactional
  mail is exempt.
- **Spam rate:** keep the user-reported rate in Postmaster Tools below 0.1%.
  At 0.3% or higher, mitigation is unavailable until it stays under 0.3% for
  seven consecutive days.
- **Enforcement:** since November 2025 Gmail has been ramping up enforcement,
  with temporary and permanent rejections for non-compliant traffic.

## Yahoo

Source: https://senders.yahooinc.com/best-practices/

Same shape as Gmail: authentication, DMARC, one-click unsubscribe honored
within two days, and a low complaint rate.

## Microsoft (Outlook.com, Hotmail, Live)

Source: Microsoft Outlook blog, "Strengthening Email Ecosystem: Outlook's New
Requirements for High-Volume Senders",
https://techcommunity.microsoft.com/blog/outlook/strengthening-email-ecosystem-outlook%E2%80%99s-new-requirements-for-high%E2%80%90volume-senders/4399730

- Applies to domains sending more than 5,000 messages a day to Microsoft
  consumer addresses, effective May 5, 2025.
- SPF, DKIM, and DMARC (p=none minimum, aligned with SPF or DKIM) must pass.
- Non-compliant mail is junked, then rejected with
  `550; 5.7.515 Access denied, sending domain does not meet the required authentication level`.
- Recommended: a working unsubscribe link, list hygiene, a reply-capable
  From or Reply-To address.

## US law

CAN-SPAM applies to commercial messages, including lifecycle promotions: no
deceptive headers or subject lines, a valid physical postal address, a clear
opt-out, and opt-outs honored within 10 business days. Source:
https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

## Launch checklist for a new sequence

- [ ] SPF, DKIM, and DMARC pass for the sending domain (read the headers of a
      real test send, do not assume)
- [ ] From domain aligned with the DKIM signing domain
- [ ] Marketing emails carry RFC 8058 one-click unsubscribe headers
- [ ] Unsubscribes reach the suppression list within 48 hours, across every
      tool that sends to the contact
- [ ] Complaint rate visible in Google Postmaster Tools and a threshold alert
      set below 0.1%
- [ ] Re-engagement flow ends by suppressing contacts who never re-engage, so
      dead addresses stop dragging the complaint and bounce rates
- [ ] Transactional and marketing streams separated (subdomain or IP) so a
      promotional complaint spike cannot block receipts and password resets
