# 검토 절차

추적 변경, 댓글, 수락, 거부. 각각이 패키지 바이트에 하는 일과 해서는 안 되는 일을 정합니다.

## 1. XML의 변경 표시

추적 변경은 텍스트 옆의 메타데이터가 아니라, 작성자와 날짜를 담은 컨테이너로 감싼 텍스트입니다.

| 요소 | 위치 | 의미 |
|---|---|---|
| `w:ins` | 문단 안 `w:r` 런을 감쌈 | 삽입된 내용. 수락하면 남음 |
| `w:del` | 문단 안 `w:r` 런을 감쌈 | 삭제된 내용. 수락하면 사라짐 |
| `w:delText` | `w:del` 안 `w:r` 안 | 삭제된 글자(`w:t`가 아님) |
| `w:pPr/w:rPr` 안 `w:ins`·`w:del` | 문단 표시 자체 | 문단 표시가 삽입·삭제됨 |
| `w:moveFrom`·`w:moveTo` | 문단 수준 | 옮긴 블록. 수락하면 `moveTo`가 남음 |
| `w:commentRangeStart`·`w:commentRangeEnd` | 문단 수준 | 댓글이 가리키는 텍스트 구간 |
| `w:commentReference` | 구간 안 런 | 구간을 `comments.xml`의 `w:comment`와 연결 |

여기서 규칙 두 개가 나오고, 둘 다 깨지기 쉽습니다.

- 삭제된 텍스트는 `w:delText`에 있고 `w:t`에 있지 않습니다. `w:del` 안 런이 여전히 `w:t`를 가지면 일부 리더가 삭제된 글자를 본문처럼 보여 줍니다.
- 모든 `w:ins`와 `w:del`은 `w:id`, `w:author`, `w:date`를 갖습니다. 하나라도 없으면 변경의 주체를 알 수 없고, 워드가 그 변경을 버릴 수 있습니다.

## 2. 단어 단위와 문단 단위 편집

검토가 문단 하나를 삭제 하나와 삽입 하나로 다시 쓰면 검토자가 실제로 고친 부분을 잃습니다. 독자는 어떤 단어가 움직였는지 볼 수 없습니다. 대신 변경 경계에서 런을 나눕니다.

1. 런의 앞부분을 별도 런으로 남깁니다.
2. 바뀐 텍스트만 `w:delText`를 담은 `w:del`로 감쌉니다.
3. 바로 뒤에 대체 텍스트를 담은 `w:ins`를 둡니다.
4. 뒷부분을 별도 런으로 남깁니다.

`replace`가 정확히 일치하는 문자열 하나에 대해 이 일을 합니다. 문단에 변경이 여러 개면 문자열마다 한 번씩 호출하고, 마지막에 `verify`를 한 번 돌립니다.

## 3. 댓글

댓글은 하나이면서 둘입니다. `word/comments.xml`의 텍스트와 본문의 구간입니다. 둘 다 있어야 하고, 하나만 있으면 댓글이 보이지 않습니다.

- 고정할 내용 앞에 `w:commentRangeStart w:id="N"`
- 그 뒤에 `w:commentRangeEnd w:id="N"`
- 끝 바로 뒤에 `w:commentReference w:id="N"`를 담은 런

댓글 파트는 본문 파트에서 오는 자체 관계와 콘텐츠 타입 override가 필요합니다. 댓글에 구간이 없거나 구간에 댓글이 없으면 `verify`가 `comment-anchors`를 `fail`로 보고합니다. 리더가 "댓글이 사라졌다"거나 "워드가 복구를 요청한다"고 말할 때 나오는 두 실패입니다.

문서에 있는 문장에 고정하고 오프셋에 고정하지 않습니다. 고정을 텍스트 기준으로 하므로 문서를 다시 빌드해도 댓글이 엉뚱한 문장에 붙지 않습니다.

## 4. 수락과 거부

수락은 삽입을 남기고 삭제를 버립니다. 거부는 삭제를 되살리고 삽입을 버립니다. 둘 다 문단 표시 컨테이너(`w:rPr/w:ins`, `w:rPr/w:del`)도 펴서, 문단 병합이 변경이 없었던 것처럼 동작하게 합니다.

정직하게 남는 실행 순서입니다.

1. `revisions <file>`로 손대기 전 종류별·작성자별 개수를 기록합니다.
2. 파일을 복사하고 그 사본에 수락을 적용합니다.
3. 원본을 복사하고 두 번째 사본에 거부를 적용합니다.
4. 세 파일을 `text`로 비교합니다. 수락본과 거부본은 각자 이름이 약속한 내용을 담고, 둘 다 변경 컨테이너를 남기지 않아야 합니다.
5. 두 출력에 `verify`를 돌립니다.

변경이 없는 파일에 수락을 적용하면 `{"insertions_kept": 0, "deletions_dropped": 0}`이 나옵니다. 실패가 아니라 정상 결과이므로, 실행이 깨졌다고 보고하지 않고 그대로 말합니다.

## 5. 두 파일 비교

`compare a.docx b.docx`는 패키지 사실(문단 수, 다이제스트)과 함께 문단 수준 차이 구간을 보고합니다. 검토가 지목한 부분만 바꿨다는 것을 증명할 때 씁니다.

| 상황 | 기대 결과 |
|---|---|
| 댓글만 추가하고 텍스트는 건드리지 않음 | `no textual differences` |
| 단어 하나 교체 | 그 문단을 담은 `replace` 구간 하나 |
| 한 절 전체 재작성 | 구간 여러 개. 전달 전에 읽어 봄 |

`compare`는 텍스트를 읽으므로 서식만 바꾼 경우 차이가 없다고 보고합니다. 요청이 "이 부분을 굵게"였다면 diff가 증거가 아니라 렌더가 증거입니다.

## 6. 보고할 내용

변경 종류별 개수, 작성자, 댓글 id와 고정 문장, 그리고 수락본·거부본이 각각 어느 파일인지 적습니다. 개수 없이 "표시했습니다"라고만 하는 검토 보고는 파일을 받은 사람이 확인할 수 없습니다.

## Sources

> Checked 2026-11-13

- ECMA-376, WordprocessingML의 변경 표시와 댓글 요소 — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, 워드 문서의 모든 변경 수락 — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-accept-all-revisions-in-a-word-processing-document
- Microsoft Learn, 워드 문서에 댓글 삽입 — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-insert-a-comment-into-a-word-processing-document
