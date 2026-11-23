# PowerPointの図の校閲

受講者がそれまでに見たものと対象ページから，図で何を読み取れるかを確かめる．線の形，図形の強調，それらの編集性を調べ，教材本体の講評と独立して点検票を作る．

## 元のページを読む

スキルのディレクトリで実行する．同じページの複数案は続けて指定できる．

```sh
python scripts/diagram_review.py prepare 点検 初案.pptx 改稿案.pptx --pages 3 4
python scripts/diagram_review.py show 点検
```

ページ画像で，線の両端・途中に何があり，囲みの内側では同じ段のどの部品が先に目に入るかを見る．点検票 `observations.json` の `observed` に読めた関係を記す．原図で読みづらい箇所は `state: issue` とし，受講者がどこで迷うかを `reader_cost` に書く．役割を読み取れるときは `clear`，判断に必要なものが欠けているときは `open`．PowerPointでの移動・再接続などの所見には独立した `editing` 欄がある．

`ids` は点検項目，`evidence` は見比べた図形のID．線ではその線と関連する対象，組では同じ組の二つ以上を挙げる．観察が同じ項目はIDをまとめられる．残す理由を講師に伝える項目には `"highlight": true` を付ける．写真・画像の内部や図全体など，自動で起票されない所見は点検フォルダーの `additional.md` に書き，同じ提出稿に含める．

## 気になった箇所を比較する

```sh
python scripts/diagram_review.py compare 点検
```

ここで原図の観察が確定し，読みづらさを記録した箇所だけが `comparisons.json` に出る．元の形と一か所を変えた形で，同じ関係をたどる．必要なら `python scripts/diagram_probe.py 初案.pptx --page 4 --id 12 --action straighten --output 比較.pptx` で両端を保った直線を作り，元と同じ表示条件で見る．矩形を縮めるときは `--action compact`．すでにある別案も比較に使える．比較画像への相対リンクは点検フォルダーの親を起点にする．

`observed` に，元の読みづらさがどう変わり，どの表現を採るかを書く．読み取りが改善したときは `result: better`，差がないときは `same`，悪化は `worse`，根拠が足りないときは `open`．変更が別の箇所を読みにくくした場合もその結果に含める．

```sh
python scripts/diagram_review.py finish 点検 提出する講評.md --main 校閲済みの本文稿.md
```

依頼元が本文稿と図の判定を照合し，食い違いがあれば該当箇所の判断を確定する．`--main` に指定した講評に，読み取りが改善した修正，指定した維持理由，編集上の所見，保留箇所が加わる．図だけを返すときは `--main` を省く．提出するファイルを同じコマンドに `--check` を加えて照合する．提出稿に加えたい修正は，対応する本文稿・点検票で校閲してから合成する．
