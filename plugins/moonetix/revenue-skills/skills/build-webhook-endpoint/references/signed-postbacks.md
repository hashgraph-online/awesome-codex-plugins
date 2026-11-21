# Query-string signed postbacks

Affiliate networks, offerwalls and ad reward systems usually report a conversion with a plain request to a URL the app registered, most often a GET. The values travel in the query string, and one parameter is a hash over some of the others and a key that only the network and the app know.

```text
https://app.example/postback/examplenet?user_id={user_id}&tx={transaction_id}&reward={reward}&status={status}&hash={hash}
```

The app chooses the path and the parameter names when it registers the URL. The network fills the placeholders. There is no body, no timestamp and usually no event id: the transaction id is the identity of the event.

## Read the formula first

Every network documents its own formula. Do not guess it and do not copy it from another network. Find these six facts in the network's documentation before writing code:

| Fact | Typical variants |
| --- | --- |
| Which fields are hashed | User id, transaction id, reward, payout, status, offer id |
| In which order | Fixed by the documentation, not by the order in the URL |
| How they are joined | A separator such as `:` or `&`, or nothing at all |
| Which function | HMAC-SHA256, SHA-256, SHA-1 or MD5 over the joined text |
| Where the key goes | As the HMAC key, or appended or prepended to the text |
| How the result is encoded | Hex, in lower or upper case |

When the network offers a choice, take the HMAC variant. When it offers only a plain hash with the key appended, use it as documented and add the second layer described under "More than the hash".

## Rules

1. **Verify over the strings as they arrived.** Build the text from the received values, after the framework's single URL decoding and before any conversion. A reward of `10.50` that was cast to a number and back is `10.5`, and the hash no longer matches.
2. **Act only on what the hash covers.** Every value the handler uses must be inside the hash: the user, the transaction id, the amount, the status. If the formula leaves one out, that value is whatever the caller wants it to be. Then either ask the network for a formula that covers it, or take the value from the app's own records. The common way: put the app's own click id into the tracking link, store user and offer under it at click time, and let the postback carry the click id back. The user then comes from the stored click, not from the query string.
3. **Validate after verifying.** Strict formats for every value: digits for ids and amounts, a short character set for the transaction id, a known list for the status. Formats also limit what a formula without separators can be bent into.
4. **No bypass.** No debug or test parameter, no "skip when the hash is absent", no test mode a caller can switch on. Test with a test key.
5. **The key has no default** and is checked before the handler runs. One key per network.

## The handler

PHP with PDO. `post_entry()` is the project's ledger posting function: it inserts under a unique (kind, reference) key and returns whether the entry was new.

```php
<?php
declare(strict_types=1);

const POSTBACK_SOURCE = 'examplenet';

/** The formula from the network's documentation. Here: HMAC-SHA256 of "user_id:tx:reward:status". */
function postback_hash(string $key, string $userId, string $tx, string $reward, string $status): string
{
    return hash_hmac('sha256', "$userId:$tx:$reward:$status", $key);
}

/**
 * @param array<string, mixed> $query the parsed query string
 * @return array{int, string} status code and body
 */
function handle_postback(PDO $db, string $key, array $query): array
{
    // A parameter sent as user_id[]=1 arrives as an array. Only strings take part.
    $param = static fn (string $name): string => is_string($query[$name] ?? null) ? $query[$name] : '';
    [$userId, $tx, $reward, $status] = array_map($param, ['user_id', 'tx', 'reward', 'status']);

    // Verify over the strings exactly as they arrived, before any conversion.
    $expected = postback_hash($key, $userId, $tx, $reward, $status);
    if (!hash_equals($expected, strtolower($param('hash')))) {
        return [403, 'BAD HASH'];
    }

    // Then check the format of every value the handler acts on.
    if (!preg_match('/^[1-9]\d{0,17}$/D', $userId)
        || !preg_match('/^[\w.:-]{1,128}$/D', $tx)
        || !preg_match('/^[1-9]\d{0,8}$/D', $reward)
        || !in_array($status, ['1', '2'], true)) {
        return [400, 'BAD REQUEST'];
    }

    $db->beginTransaction();
    try {
        if ($status === '2') {
            // Takes back what this transaction id credited, not the amount in this request.
            reverse_conversion($db, POSTBACK_SOURCE, $tx);
            $body = 'OK';
        } else {
            $known = $db->prepare('SELECT 1 FROM accounts WHERE id = ?');
            $known->execute([(int) $userId]);
            if ($known->fetchColumn() === false) {
                $db->rollBack();
                return [404, 'UNKNOWN USER'];
            }
            $posted = post_entry($db, accountId: (int) $userId, amount: (int) $reward, kind: 'offer_' . POSTBACK_SOURCE, ref: $tx);
            $body = $posted ? 'OK' : 'DUPLICATE';
        }
        $db->commit();
    } catch (Throwable $e) {
        $db->rollBack();
        throw $e;
    }
    return [200, $body];
}
```

The entry point checks the key and passes the query on:

```php
$key = getenv('POSTBACK_KEY');
if (!is_string($key) || strlen($key) < 16) {
    http_response_code(500);   // no key, no credit: never fall back to a default
    exit;
}
[$code, $body] = handle_postback($db, $key, $_GET);
http_response_code($code);
header('Content-Type: text/plain');
echo $body;
```

Notes on the code:

- `hash_equals` compares in constant time. The received hash is lower-cased because `hash_hmac` returns lower-case hex and some networks send upper case.
- The `D` modifier keeps `$` from matching before a trailing line break.
- The amount pattern refuses zero, a sign, a fraction and anything longer than nine digits. If the network sends decimal amounts, verify over the string, then convert with a decimal function to the app's smallest unit. Never use a float.
- `reverse_conversion()` is the project's reversal function. A reversal takes back what the original transaction credited. Building it is the subject of the `handle-refunds-and-reversals` skill. Until it exists, answer a reversal with a 5xx status so the network counts it as undelivered, log it, and tell the user that reversals are not handled yet. Never answer 200 to a reversal that was dropped.

## Once per transaction

A postback has no timestamp. A URL that was valid once is valid forever, and it sits in access logs on both sides. The only replay protection is the memory of the transaction id, and that memory must never expire.

With a ledger, the unique key does it: one kind per network (`offer_examplenet`) and the transaction id as the reference. Two networks can issue the same id, which is why the network is part of the key.

Without a ledger, use a table whose primary key is (network, transaction id), written in the same transaction as the balance update:

```sql
BEGIN;
INSERT INTO credited_transactions (source, tx_id, account_id, amount)
VALUES ('examplenet', :tx, :user, :reward)
ON CONFLICT (source, tx_id) DO NOTHING;
-- Only when the insert reported one row:
UPDATE users SET balance = balance + :reward WHERE id = :user;
COMMIT;
```

MySQL has no `ON CONFLICT`: use a plain `INSERT` and treat error 1062 as "seen before". Do not use `INSERT IGNORE`, which hides other failures too.

Copies of one postback do arrive at the same moment. The key decides, not a `SELECT` before the insert.

## Status values

Networks report more than completions. Map each documented status to one action and refuse the rest.

| Meaning | Action |
| --- | --- |
| Conversion approved | Credit once, keyed by the transaction id |
| Conversion reversed, charged back or rejected after approval | Reverse what that transaction id credited |
| Pending, to be confirmed later | No credit. Show it as pending if the app has such a display |
| Anything undocumented | 400, and a log line |

## The amount

- Take it from the signed parameter the network documents as the user's reward, or compute it on the server from the signed payout and the app's own rate. Never from an unsigned parameter.
- Know the unit. A reward in the app's points is an integer. A payout in currency needs a decimal conversion and a rounding rule, decided once.
- Set a cap per event with the user. A postback above the cap is stored and held for a person instead of credited. A leaked key is then worth less, and a misconfigured offer is caught on the first event.

## What to answer

Networks decide between "delivered" and "retry" by the status code, and some also by the body, expecting a fixed text such as `OK` or `1`. Check the network's documentation.

- Success and duplicate both get the success answer. A duplicate that is answered with an error is retried for days.
- A failed hash gets 403 and nothing else.
- An unknown user is permanent. Answer the way the documentation says stops retries, and log it.
- A database failure gets 5xx, so the network sends the postback again.

## More than the hash

- **Sender addresses.** When the network publishes the addresses its postbacks come from, check the socket peer against them as a second layer. Behind a proxy, read the forwarding header only when the peer is that proxy. The hash stays mandatory.
- **Logs.** The full URL, hash included, is in the web server's access log. Anyone who can read the log can replay a postback, which is harmless only because of the transaction key. Restrict the log like any other file with credentials in it.
- **A static token instead of a hash.** Some networks can only append a fixed secret to the URL. Compare it in constant time and treat it as a password: every value in the request is then unsigned, so cap the amount, keep the address check, and reconcile against the network's reports.
- **Key rotation.** Few networks support an overlap. Accept the old and the new key side by side for the switch, as with header signatures, and remove the old one the same day.
- **Reconciliation.** Compare the credited totals per network and day with the network's own report. A postback endpoint that credits more than the report shows is being fed from somewhere else.
