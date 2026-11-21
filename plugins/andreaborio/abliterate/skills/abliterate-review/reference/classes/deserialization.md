# Unsafe deserialization and parser abuse (CWE-502, CWE-611, CWE-1321, CWE-1333)

## Sources
- Request bodies and cookies (serialized sessions, "remember me" blobs, Java `rO0` / .NET `AAEAAAD` / PHP `O:` looking values), uploaded files (YAML, XML, Office/SVG/ZIP-in-XML), message queue payloads, cache entries that a lower-privileged service can write, imported backups.
- JSON bodies merged into objects: `req.body`, query objects from `qs` (`a[__proto__][x]=1`).
- Regex input: any string matched against a pattern with nested/ambiguous quantifiers, especially usernames, emails, URLs, markdown, headers.

## Sinks
| Class | Stack | Sink | Safe alternative |
| --- | --- | --- | --- |
| 502 | Python | `pickle.load(s)`, `marshal.loads`, `shelve`, `yaml.load` without `SafeLoader` (or `Loader=yaml.Loader/UnsafeLoader`), `jsonpickle.decode`, `torch.load` on untrusted files (weights_only where supported) | `json`, `yaml.safe_load`, signed+verified blobs |
| 502 | Java | `ObjectInputStream.readObject`, `XMLDecoder`, `XStream` without allowlist, Jackson `enableDefaultTyping`/`@JsonTypeInfo(use=CLASS)`, `SnakeYAML new Yaml()` on untrusted data | JSON to a fixed DTO; `ObjectInputFilter` allowlist; `SafeConstructor` |
| 502 | PHP | `unserialize($input)`, phar:// file operations on user paths | `json_decode`; `unserialize($s, ['allowed_classes'=>false])` |
| 502 | .NET | `BinaryFormatter`, `SoapFormatter`, `NetDataContractSerializer`, `LosFormatter`, Json.NET `TypeNameHandling != None` | `System.Text.Json`, fixed types |
| 502 | Ruby | `Marshal.load`, `YAML.load` (check Psych version defaults), `Oj.load` in object mode | `JSON.parse`, `YAML.safe_load` |
| 502 | Node | `node-serialize` `unserialize`, `eval`-based "JSON" parsers, `js-yaml` custom unsafe schemas | `JSON.parse`, `yaml` safe schema |
| 611 | Java | `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`, `TransformerFactory` with default features | disable DTD: `disallow-doctype-decl`, secure-processing, `ACCESS_EXTERNAL_DTD=""` |
| 611 | Python | `lxml.etree` with `resolve_entities` true / `XMLParser(load_dtd=True)`, `xml.sax`, stdlib `xml.etree` (billion laughs) | `defusedxml`, `XMLParser(resolve_entities=False, no_network=True)` |
| 611 | PHP / .NET / Node | `simplexml_load_string` with `LIBXML_NOENT`, `XmlDocument` with `XmlResolver` set, `libxmljs` with `noent:true` | do not enable entity substitution; `DtdProcessing.Prohibit` |
| 1321 | JS | recursive merge/`_.merge`, `lodash.set/defaultsDeep`, `Object.assign` into nested, `JSON.parse` result merged with user keys, `obj[a][b] = v` with user keys | `Object.create(null)`, `Map`, reject `__proto__`/`constructor`/`prototype` keys, `structuredClone`, schema-validated shapes |
| 1333 | any | regex with nested quantifiers `(a+)+`, `(.*)*`, overlapping alternations `(a\|a)*`, `.*.*` on user input; backtracking engines (JS, Python `re`, Java, PCRE, Ruby < 3.2) | linear engine (RE2 / Go `regexp` / Rust), length cap before match, timeouts (Ruby `Regexp.timeout`), rewrite pattern |

## Guards that work / Look-alike guards
Work:
- Never feed untrusted bytes to a native-object deserializer; use a data format into a fixed schema.
- Allowlist of classes at the deserializer (`ObjectInputFilter`, `allowed_classes`), applied process-wide where possible.
- Authenticate before deserializing: HMAC/signature over the blob with a server-held key, verified before parse (constant-time compare).
- XML parser features turned off at construction, for every parser instance on the path.
- Key denylist for merges plus prototype-less targets.
- Input length cap before regex matching.

Look-alike:
- Validating the object after `unserialize`/`readObject` (gadgets run during deserialization).
- Blocklisting known gadget classes.
- Encrypting without authenticating (malleable), or signing with a key readable by the client.
- Disabling external entities but leaving DTDs/parameter entities or XInclude on; setting the feature on one factory while another is used.
- Prototype pollution guard that checks only top-level `__proto__` and not `constructor.prototype` or nested paths.
- Regex "validated" on short samples only; anchors `^...$` do not remove backtracking.

## Falsify before reporting
1. Can the attacker reach the bytes: request, cookie, upload, or only internal trusted storage? Who writes the queue/cache?
2. Is the deserializer actually the unsafe mode (loader class, flags, typing) in the pinned library? `yaml.load(x, Loader=SafeLoader)` is safe.
3. Is the blob authenticated before parsing, with a key the attacker cannot obtain?
4. XXE: is the parser the one fed with user XML, and are DTD/external-entity features off at that instance (check factory construction, not a shared util elsewhere)?
5. Prototype pollution: does the polluted property later gate behavior (authorization flag, template option, spawn option)? Pollution without a reachable gadget is low.
6. ReDoS: can a crafted input of realistic size (request body limit) cause super-linear time on this engine? Check the regex and the engine; cite the ambiguous quantifier.
7. Confirm: a test submits a benign marker object/entity (a document declaring an entity pointing at a temp file inside the test) and asserts it is rejected or not resolved.

## Severity cues
- Raises: unauthenticated, native object graph with gadget libs on classpath, server runs with cloud credentials; XXE with file/SSRF read; pollution reaching auth or process-spawn options.
- Lowers: blob signed with server-only key, admin import only, parser limited to a safe subset, ReDoS needs inputs above the body-size limit, availability-only impact.

## Regression test
- 502: feed a benign marker (a pickle/YAML tag invoking a harmless test function that records a call, in the test only) and assert it is not invoked and the request is rejected; a plain JSON/YAML document still loads.
- 611: XML with an internal DOCTYPE entity; assert the entity is not expanded and no file/network read happens; ordinary XML parses.
- 1321: `{"__proto__": {"polluted": true}}` merged; assert `({}).polluted === undefined` afterwards and the legitimate keys merge.
- 1333: time the match on a 30-char near-miss string against a threshold, or assert the length cap rejects it; normal input matches as before.
