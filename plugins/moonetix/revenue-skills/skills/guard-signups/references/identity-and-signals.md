# Identity and signals

What a sign-up attempt tells you before the account exists: an email address and a network address. This file turns both into values the rest of the build can key on.

## The normalized email

`jane.doe@gmail.com`, `janedoe+1@gmail.com` and `J.A.N.E.Doe@googlemail.com` are three strings and one inbox. A unique index on the typed string treats them as three people. Key uniqueness on a normalized form instead, and keep sending mail to the address the user typed.

Apply a rule only where the mailbox provider documents it. A guess merges two real people into one account key, and that person cannot sign up.

| Provider | Domains | Plus tag removed | Dots removed | Other |
| --- | --- | --- | --- | --- |
| Gmail | gmail.com, googlemail.com | yes | yes | googlemail.com becomes gmail.com |
| Proton Mail | proton.me, protonmail.com, protonmail.ch, pm.me | yes | no | Domains are not merged |
| Fastmail | fastmail.com, fastmail.fm | yes | no | `tag@user.fastmail.com` becomes `user@fastmail.com` |
| Yandex Mail | yandex.com, yandex.ru | yes | no | |
| Every other domain | | no | no | Lowercase only |

Notes that keep this table honest:

- Check each provider's current help pages before adding or changing a row. The table reflects what the providers documented in November 2026.
- Custom domains hosted by Google keep their dots. The Gmail rules apply to the two Gmail domains only.
- Outlook.com, iCloud and Yahoo are lowercased only. Microsoft documents plus addressing for organizations on Exchange Online, not for consumer accounts. Third-party guides say consumer Outlook.com delivers plus-tagged mail as well, so the sources conflict: keep the tag by default, and if the sign-up data shows `+` variants farming one outlook.com or hotmail.com mailbox, add those domains to `plusTagDomains`. Yahoo's disposable addresses do not contain the account name. If the user wants plus tags removed for more domains, make it a list in configuration (`plusTagDomains` below), not a blanket rule.
- A domain with a catch-all mailbox yields unlimited addresses that no normalization can merge. Verification and velocity handle those, and so can a count of sign-ups per email domain for domains outside the large public providers.

Node:

```js
// Rules are applied only where the mailbox provider documents them.
const PROVIDERS = [
  { domains: ['gmail.com', 'googlemail.com'], canonical: 'gmail.com', plus: true, dots: true },
  { domains: ['proton.me', 'protonmail.com', 'protonmail.ch', 'pm.me'], plus: true },
  { domains: ['fastmail.com', 'fastmail.fm'], plus: true, subdomainIsUser: true },
  { domains: ['yandex.com', 'yandex.ru'], plus: true },
];

const LOCAL = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*$/;
const DOMAIN = /^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,61}[a-z0-9]$/;

// Returns { normalized, domain } for the uniqueness key, or { problem } for input to reject.
// Mail is still sent to the address the user typed.
export function normalizeEmail(input, { plusTagDomains = [] } = {}) {
  if (typeof input !== 'string') return { problem: 'not_a_string' };
  const email = input.trim().toLowerCase();
  if (email.length > 254 || !/^[\x21-\x7e]+$/.test(email)) return { problem: 'invalid' };
  const at = email.lastIndexOf('@');
  if (at < 1 || email.indexOf('@') !== at) return { problem: 'invalid' };
  let local = email.slice(0, at);
  let domain = email.slice(at + 1);
  if (local.length > 64 || !LOCAL.test(local) || !DOMAIN.test(domain)) return { problem: 'invalid' };

  let rule = PROVIDERS.find((p) => p.domains.includes(domain));
  if (!rule) {
    const parent = domain.slice(domain.indexOf('.') + 1);
    const host = PROVIDERS.find((p) => p.subdomainIsUser && p.domains.includes(parent));
    if (host) {
      // tag@user.fastmail.com is delivered to user@fastmail.com
      local = domain.slice(0, domain.indexOf('.'));
      domain = parent;
      rule = host;
    }
  }
  if (rule?.plus || plusTagDomains.includes(domain)) local = local.split('+')[0];
  if (rule?.dots) local = local.replaceAll('.', '');
  if (rule?.canonical) domain = rule.canonical;
  if (local === '') return { problem: 'invalid' };
  return { normalized: `${local}@${domain}`, domain };
}

// True when the domain or one of its parent domains is on the list. allow wins over the list.
export function isDisposable(domain, disposable, allow = new Set()) {
  const labels = domain.split('.');
  for (let i = 0; i < labels.length - 1; i += 1) {
    const candidate = labels.slice(i).join('.');
    if (allow.has(candidate)) return false;
    if (disposable.has(candidate)) return true;
  }
  return false;
}
```

Python, same behavior:

```python
import re

# Rules are applied only where the mailbox provider documents them.
PROVIDERS = [
    {"domains": {"gmail.com", "googlemail.com"}, "canonical": "gmail.com", "plus": True, "dots": True},
    {"domains": {"proton.me", "protonmail.com", "protonmail.ch", "pm.me"}, "plus": True},
    {"domains": {"fastmail.com", "fastmail.fm"}, "plus": True, "subdomain_is_user": True},
    {"domains": {"yandex.com", "yandex.ru"}, "plus": True},
]

ATOM = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
LOCAL = re.compile(rf"{ATOM}(\.{ATOM})*")
DOMAIN = re.compile(r"([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,61}[a-z0-9]")


def normalize_email(value, plus_tag_domains=()):
    """Returns (normalized, domain) for the uniqueness key, or (None, None) for input to reject."""
    if not isinstance(value, str):
        return None, None
    email = value.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[\x21-\x7e]+", email) or email.count("@") != 1:
        return None, None
    local, domain = email.split("@")
    if not 0 < len(local) <= 64 or not LOCAL.fullmatch(local) or not DOMAIN.fullmatch(domain):
        return None, None

    rule = next((p for p in PROVIDERS if domain in p["domains"]), None)
    if rule is None:
        user, _, parent = domain.partition(".")
        host = next((p for p in PROVIDERS if p.get("subdomain_is_user") and parent in p["domains"]), None)
        if host:
            # tag@user.fastmail.com is delivered to user@fastmail.com
            local, domain, rule = user, parent, host
    if (rule and rule.get("plus")) or domain in plus_tag_domains:
        local = local.split("+")[0]
    if rule and rule.get("dots"):
        local = local.replace(".", "")
    if rule and rule.get("canonical"):
        domain = rule["canonical"]
    if not local:
        return None, None
    return f"{local}@{domain}", domain
```

Both reject anything that is not plain ASCII. If the product must accept internationalized addresses, convert the domain to its ASCII form and apply Unicode NFC to the local part before lowercasing, and test that path separately.

Keep test vectors next to the code, and run the same vectors against every implementation in the project. A minimum set: the three Gmail strings above give `janedoe@gmail.com`; `erin+tag@outlook.com` is unchanged; `first.last@a-custom-domain.com` keeps its dot; `kim@@example.org`, `kim@example` and `+tag@gmail.com` are rejected.

### Schema and backfill

```sql
ALTER TABLE users ADD COLUMN email_normalized TEXT;
CREATE UNIQUE INDEX users_email_normalized_key ON users (email_normalized);
```

The column is nullable on purpose. A unique index accepts any number of NULLs in PostgreSQL, MySQL and SQLite, which is what makes a backfill possible on a table that already holds duplicates:

1. Add the column and the index. New sign-ups write the key from now on.
2. In batches, compute the key for existing rows in application code (the same function as sign-up, never a second implementation in SQL). Process accounts oldest first. When the write fails on the unique index, leave that row's key NULL and flag the account as a duplicate of the older one (a nullable `duplicate_of` column is enough).
3. Report the collision groups to the user before taking any action on them. Flagged accounts keep working. They get no further bonuses or trials.

Every path that creates an account or changes its email must write the key in the same statement as the address. Search for all of them: social login, invitations, admin tools, imports, the change-email flow.

### Disposable domains

Disposable inbox services hand out working addresses on thousands of domains. The public `disposable-email-domains` list (CC0, on GitHub under the same name) tracks them. Store a copy with the application, load it into a set at start-up, and refresh it with a scheduled job that refuses to install a list that failed to download or shrank by more than half. Never fetch a list during a sign-up request.

Check the domain and each parent domain, never the bare top-level domain, as `isDisposable` above does: `inbox.mailinator.com` is disposable because `mailinator.com` is. Keep two small lists of your own: `allow` for domains your users prove wrong, and extra blocked domains you find in your own data. The list's maintainers do not guarantee every entry, so the allow list will be used.

## The client address

Every address check depends on reading the visitor's address and not your own infrastructure. Behind a reverse proxy, load balancer or CDN, the TCP peer is that proxy. The visitor's address is in a header the proxy sets, and that header is trustworthy only when the request really came from the proxy. From anyone else it is text the sender chose.

- If the framework has a trusted proxy setting, configure it with the proxy's addresses and use the framework's client address. Do not set it to "trust everything".
- Otherwise read the header yourself, as below. For `X-Forwarded-For`, walk from the right and take the first address that is not one of your proxies; entries on the left were supplied by the client.
- A client address that is private, loopback or carrier-grade NAT space in production means the setup is wrong. Skip the address rules for that request and log loudly. Counting it would put every user under one velocity limit.

```js
import net from 'node:net';

const subnets = (cidrs) => {
  const list = new net.BlockList();
  for (const cidr of cidrs) {
    const [address, bits] = cidr.split('/');
    list.addSubnet(address, Number(bits), net.isIPv6(address) ? 'ipv6' : 'ipv4');
  }
  return list;
};
const contains = (list, ip) => list.check(ip, net.isIPv6(ip) ? 'ipv6' : 'ipv4');

// Private, loopback, link-local and carrier-grade NAT space. A client address in here
// means the app is reading its own proxy, not the visitor.
const NOT_PUBLIC = subnets([
  '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8', '169.254.0.0/16', '100.64.0.0/10',
  '::1/128', 'fc00::/7', 'fe80::/10',
]);

// "::ffff:203.0.113.9" from a dual-stack socket is the IPv4 address 203.0.113.9.
export function canonicalIp(value) {
  const text = String(value ?? '').trim().replace(/^::ffff:(?=\d+\.\d+\.\d+\.\d+$)/i, '');
  if (net.isIPv4(text)) return text;
  if (!net.isIPv6(text)) return null;
  return new net.SocketAddress({ address: text, family: 'ipv6' }).address;
}

// The address of the visitor. Forwarding headers count only when the TCP peer is one of
// your own proxies; from anyone else they are text the sender chose.
export function clientAddress(req, isTrustedProxy) {
  let ip = canonicalIp(req.socket.remoteAddress);
  if (!ip || !isTrustedProxy(ip)) return ip;
  const hops = String(req.headers['x-forwarded-for'] ?? '').split(',');
  while (hops.length) {
    const hop = canonicalIp(hops.pop());
    if (!hop) break;
    ip = hop;
    if (!isTrustedProxy(ip)) break;
  }
  return ip;
}

// IPv4 /24 or IPv6 /64: one home, office or campus, whichever address it uses today.
export function networkPrefix(ip) {
  if (net.isIPv4(ip)) return `${ip.split('.').slice(0, 3).join('.')}.0/24`;
  const [head, tail] = ip.split('::');
  const left = head ? head.split(':') : [];
  const right = tail ? tail.split(':') : [];
  const groups = tail === undefined ? left : [...left, ...Array(8 - left.length - right.length).fill('0'), ...right];
  return `${groups.slice(0, 4).join(':')}::/64`;
}

// lists: { datacenter: [cidr, ...], tor: [...], relay: [...], cdn: [...] }, loaded once at start-up.
export function createClassifier(lists) {
  const categories = Object.entries(lists).map(([name, cidrs]) => [name, subnets(cidrs)]);
  return (ip) => {
    if (!ip) return { public: false, categories: [] };
    if (contains(NOT_PUBLIC, ip)) return { public: false, categories: [] };
    return { public: true, categories: categories.filter(([, list]) => contains(list, ip)).map(([name]) => name) };
  };
}
```

`networkPrefix` expects the output of `canonicalIp`. In Python the standard `ipaddress` module covers all of this: `ip_address(text)`, `.ipv4_mapped`, `.is_global`, `ip in ip_network(cidr)`, and `ip_network(f"{ip}/64", strict=False)` for the prefix. In PHP, compare `inet_pton` results under a bit mask.

## Address categories

| Category | Where the ranges come from | What a match means |
| --- | --- | --- |
| `datacenter` | The feeds cloud and hosting providers publish about themselves for firewalls and allow lists | People rarely browse from a rented server. Scripts usually do. Some real users do too: cloud desktops, company VPN gateways. |
| `tor` | The Tor Project's exit list | Tor Browser users and automation on Tor. |
| `relay` | The egress ranges Apple publishes for iCloud Private Relay | Real Safari users. Many people share one address. |
| `cdn` | The edge ranges CDNs publish | Usually a proxy or worker in front of the browser. Weak signal. |

Use the providers' own feeds and read each feed's terms. Keep `tor` and `relay` as separate lists from `datacenter`, because they carry real users and get a different weight. Refresh with the same guarded job as the disposable list.

What these lists do not cover: hosts that publish no feed, most commercial VPNs, and all residential proxies, which exit through home connections. Range checks stop the cheapest automation. They are a signal for the score, never a verdict. Do not apply them to webhook or postback endpoints: those callers are servers by design.
