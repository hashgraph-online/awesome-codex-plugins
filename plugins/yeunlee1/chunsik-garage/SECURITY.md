# Security policy / 보안 정책

## Reporting a vulnerability

Please report a security problem privately. Open the **Security** tab of this repository and choose **Report a vulnerability**. Do not put the details in a public issue.

We will answer in the private report. A fix goes out in the next release, and the release notes say what it fixed.

## Supported versions

Only the latest release on the `main` branch gets security fixes. To update, follow the update steps in the README.

## What the program touches

- The program and the report page make no network requests. They read your local Claude Code and Codex records and settings on your PC.
- The program never prints the value of an API key or token it finds in your settings. It prints only where the key is written.
- The tune-up changes only the items you approve, writes a record first, and can undo each change.

---

## 취약점 알리기

보안 문제는 비공개로 알려 주세요. 이 저장소의 **Security** 탭에서 **Report a vulnerability**를 고르면 됩니다. 자세한 내용을 공개 이슈에 적지 마세요.

답은 비공개 신고 안에서 드립니다. 고친 것은 다음 배포에 담고, 배포 안내에 무엇을 고쳤는지 적습니다.

## 지원하는 버전

`main` 브랜치의 최신 배포만 보안 수정을 받습니다. 업데이트는 README의 업데이트 방법을 따릅니다.

## 프로그램이 건드리는 것

- 프로그램과 결과 화면은 네트워크로 요청을 보내지 않습니다. 내 PC에 있는 Claude Code와 Codex의 기록과 설정을 읽습니다.
- 설정에서 찾은 API 키나 토큰의 값은 내놓지 않습니다. 어디에 적혀 있는지만 내놓습니다.
- 정비는 승인한 것만 바꾸고, 기록을 먼저 남기고, 하나씩 되돌릴 수 있습니다.
