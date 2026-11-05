---
name: codex-session-edit-audit
description: Use when the user asks Codex to reconstruct or review what happened earlier in the same thread/session, especially to list actual edits, mistaken edits, reverted edits, tool calls, or the sequence that led to the current state. The skill directs Codex to inspect Codex session history as the primary record of past actions.
---

# Codex Session Edit Audit

## Purpose

過去の振り返り、編集履歴の列挙、誤操作の確認、会話中の作業経緯の説明を求められたときに使う。Codex の session 履歴を一次確認対象にし、現在の作業ツリーや git は補助資料として扱う。

## Required Behavior

- まず `${CODEX_HOME:-$HOME/.codex}/sessions` 配下の関連 session JSONL を探す。
- session ファイルのディレクトリ日付だけで判断しない。mtime と JSONL 内の timestamp を確認する。
- session 内の `apply_patch`、`exec_command`、ファイル生成、削除、上書き、ビルド、検証コマンドを時系列で追う。
- 編集してから戻した内容、一時生成物、削除済みファイルも作業履歴として扱う。
- git の確認は現在残っている差分や作業ツリー状態の補助確認に限る。
- ユーザが「今日」「さっき」「このスレッド」と言った場合は、session timestamp とローカルタイムゾーンの対応を明示する。
- 監査だけを求められている間は、新規編集、復元、整形、クリーンアップを行わない。

## Efficient Review Procedure

1. 監査範囲を決める。
   - ユーザが指定した相対時刻、日付、対象ファイル、発言内容、作業ディレクトリをメモする。
   - 「今日」などのローカル日付は UTC の範囲に変換してから session timestamp と照合する。

2. session 候補を絞る。
   - `${CODEX_HOME:-$HOME/.codex}/sessions` 配下の `*.jsonl` を mtime の新しい順に見る。
   - ディレクトリ名の日付は候補探索の手がかりに留める。session ファイルが古い日付ディレクトリに保存される場合がある。
   - 候補が複数ある場合は、JSONL 内の user 発言、対象 path、cwd、tool call の timestamp が監査範囲と合うものを優先する。
   - 「このスレッド」は、直近の user / assistant message が現在の会話内容と連続している session を優先する。
   - 同じ対象 path が複数 session に出る場合は、該当 user 発言と後続 tool call が同じ session 内で連続しているものを採用する。確定できない場合は候補を列挙して未確認点に残す。
   - 同程度に一致する候補を無理に一つへ絞らない。根拠付きで候補を並べ、どこまで確認したかを書く。
   - 候補探索は、指定範囲を含む session が見つかり、その前後の user 発言と tool call の対応が確認できた時点で止める。対象 path が別 session にも出る場合だけ追加確認する。

3. session を時系列で読む。
   - JSONL の各 record の `timestamp` と line number を控える。
   - 関連 tool call の直前直後の user / assistant message も読む。何を依頼され、なぜその編集をしたかを確認する。
   - tool call だけを抜き出して判断しない。前後の発言で「戻せ」「余計なことをするな」などの意図変更が起きる。
   - 調査対象の user 発言から、次の user 発言で話題が変わるまでを最小範囲として読む。revert や追加質問が続く場合は、その連続区間の終端まで読む。

4. ファイル変更に関係する tool call を拾う。
   - `custom_tool_call` の `apply_patch`: `Update File`、`Add File`、`Delete File` を対象ファイルとして記録する。
   - `function_call` の `exec_command`: shell コマンド内の書き込み、生成、削除、移動、コピーを確認する。
   - 代表的な書き込みパターン: `cat > file`、`cat >> file`、heredoc、`tee`、`sed -i`、`perl -pi`、`python` 経由の `open(..., "w")` / `write_text`、`rm`、`mv`、`cp`、`mkdir`。
   - フォーマット、ビルド、テスト、launch、compile check はファイル編集と分けて記録する。生成物を作る可能性がある場合だけ副産物として扱う。

5. 変更の寿命を追う。
   - 同じ path への後続の上書き、削除、revert、再作成を確認する。
   - 「作った時刻」「戻した時刻」「現在残っているか」を分けて書く。
   - 現在残っていない編集も、session 履歴で確認できた作業として報告する。

6. 現在状態を補助確認する。
   - 必要な場合だけ `git status`、`git diff`、対象ファイルの現物確認を行う。
   - この確認は「今残っている状態」を説明するために使う。過去に何をしたかは session 履歴を根拠にする。

## Session Log Reading Notes

- `response_item.payload.type == "custom_tool_call"` かつ `name == "apply_patch"` は直接の patch 編集を示す。
- `response_item.payload.type == "function_call"` かつ `name == "exec_command"` は shell 経由の操作を示す。
- `exec_command` には `cat > file`、heredoc、`tee`、`sed -i`、`rm`、`mv`、`cp`、`python -m py_compile`、`colcon build` などが含まれ得る。
- JSONL の timestamp は UTC のことがある。必要に応じてユーザ環境の timezone に変換する。
- timezone は会話の環境情報、`TZ`、system timezone の順に確認する。確認できない場合は UTC のまま示し、timezone が未確認であることを書く。

## Response Format

必要に応じて以下を簡潔に出す。

- `監査対象`: 確認した session log path と時間範囲。
- `確認できた編集`: timestamp、tool call、対象 path、操作内容。
- `戻された編集`: 作成・変更された時刻と、後続操作で戻された時刻。
- `副産物`: `__pycache__`、ビルド生成物、一時ファイルなど。
- `現在残っている状態`: git やファイル確認を補助的に使った結果。
- `未確認点`: session が見つからない、ログが途中、複数 session が候補、など。

## Tone

責任確認の文脈では、推測で埋めない。session 履歴で確認できた事実と、未確認の点を分けて書く。余計な修正や周辺作業は行わず、まず履歴の確認結果を返す。
