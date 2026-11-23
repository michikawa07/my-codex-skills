# PowerPointの編集単位

PowerPointの作成・編集時に使う．ファイルの生成・変換・表示検証は該当形式の専用ツールに従う．

## 指定どおりの修正

[指定編集](../scripts/pptx_edit.py)に元資料とページを渡す．対象と変更値が分かる場合は，一度の呼び出しで適用・保存値の照合・画像出力まで行う．例えば次は「Overview」と書いた図形の回転角を15度にする例である（PowerPointでは1度が60000）．

```sh
python pptx_edit.py slides.pptx 3 attrs './/p:sp[.//a:t="Overview"]/p:spPr/a:xfrm' rot=900000 --preview-dir .
```

対象を探すときは，依頼にある文字や図形の種類で候補を絞る．`attrs XPath` に変更値を付けずに実行すると，候補の図形名・所属グループ・現在値が分かる．複製した部品には元の名前が残り，描き直した部品には別の名前が付くことがある．図形名で見つけた候補も，依頼の指す位置・向き・接続先などと照合して選ぶ．

変更する値はPowerPointのXML属性で指定する．既定の対象件数は1件．複数件なら `--count 件数`，条件に合う全件なら `--all` を使う．出力には対象と変更前後の値が載る．グループ内を含む図形一覧は `inspect`，指定図形のXMLは `inspect ID …` で確認できる．`inspect --links` はページ順とそのページへの参照・そこからの参照も返す．

ページ構成も元のページ番号で指定する．`3 omit 7-9` は3枚目と7〜9枚目を削除し，`2 keep 4-6 --output 抜粋.pptx` は2枚目と4〜6枚目を別の資料に抜き出す．残すページから外すページへリンクがあるときは，その参照先も含めて `edit_file` で編集する．

ページのXML構造を編集する場合は，スキルの `scripts` をPythonの検索先に入れ，`edit_pages(元資料, ページ番号またはリスト, change, check, preview_dir=出力先)` を呼ぶ．`change(ページ番号, XML)` で編集し，`check(ページ番号, 保存後のXML)` で成立すべき条件を返す．`shape_xml(XML, ID)` で対象の図形が取れる．画像などの関連ファイルやページ構成の変更は `edit_file(元資料, 表示するページ, write, check, preview_dir=出力先)` を使う．`write(元資料のパス, 候補の保存先)` で候補を作り，`check(保存した候補のパス)` で依頼の結果と保つべき内容を照合する．いずれも実際に保存した候補を検査してから画像を出し，元資料に反映する．

既存の短縮形は，元資料とページの後に `size "対象の全文" ポイント`，`text "旧文" "新文"`，`after 移動先の元ページ番号`，`after-last-title "見出しの冒頭"` を続ける．[ポイント指定の編集](../scripts/pptx_font_size.py)では `入力.pptx --slide 4 --title --points 32 --preview p4.png` のようにタイトル枠を指定できる．図形IDなら `--id 7`，枠の全文なら `--text "対象の全文"` を使う．

## 部品の作り方と確認

- 図形を作るときは，グループも，中の文字枠・画像・線も含め，すべてに対象や役割が分かる図形名を付ける（python-pptxでは `shape.name`）．例えばポンプの図なら，グループは「循環ポンプ」，出口の矢印は「吐出方向」と名付ける．
- 後で一度に直したいものを一つの編集単位にする．輪郭と中身が一緒に動く部品なら，一つの図形の塗り・枠線色・線幅で作る．文字はその図形に入力し，余白・段落・行間で整える．複数の可動部品からなる図は，編集者が選択・グループ化できる状態にする．
- 経路や接続先を変える矢印は，一本の標準コネクタにする．直線・折れ線・曲線は実際の経路に合わせ，矢じりは線端の種類・サイズで調整する．図形の移動に追随させる端は，その図形の接続点に結ぶ．
- 同じ役割の既存部品と設定を再利用する．文字・塗り・線のテーマ色，マスター上の書式，自動のページ番号を引き継ぐ．編集可能な本文・図形・線と，写真などの画像素材は用途に応じて使い分ける．

**校閲後の修正．** 校閲役が読んだPPTXのコピーと，提出する候補を[比較する](../scripts/diff_pptx.py)．出力にある2ファイルのSHA-256で版を特定し，変更ページ，本文の前後，画像・グラフなどの差し替えをたどる．文書プロパティや保存のたびに振り直される識別子は比較から除く．ページを特定できない差や見た目の違いは，その版を表示して確かめる．差分から影響先を選び直すのは校閲役の仕事である．

```sh
python scripts/diff_pptx.py reviewed.pptx candidate.pptx
```

提出するPPTXを保存してから，文字サイズの変更やコネクタの経路変更など，依頼者が行う操作を確かめる．表示で文字幅や重なりに差が出たら，閲覧環境のフォント・描画も調べる．

**図形内での文字の折り返し．** 図形・テキストボックスを作る共通処理で折り返しをオンにする（python-pptxでは `text_frame.word_wrap = True`）．書き出したPPTXの明示設定は `wrap="square"` になる．検査では明示オン，明示オフ，未指定を区別する．手動改行や自動サイズの設定は別に扱う．行が増えたら，全対象ページを表示し，文字サイズを保って枠の幅・高さ・配置を整える．[PowerPointの折り返し設定](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.textframe2.wordwrap)・[PPTXの属性仕様](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.bodyproperties.wrap?view=openxml-3.0.1)

[折り返しの検査・設定](../scripts/pptx_text_wrap.py)は，保存済みの図形の文字枠を確認する．新規資料は全ページを検査する．作成したページにまとめて設定するときは，例えば次のようにコピーを書き出し，提出版で確認する．同じページの一部だけを編集する場合は，対象図形の作成処理で設定する．

```sh
python scripts/pptx_text_wrap.py draft.pptx
python scripts/pptx_text_wrap.py draft.pptx --slides 2 5 --output wrapped.pptx
```

**図の部品を後でまとめて動かせるか．** 書き出し時に，普通の図形にもグループ化を禁止する設定が付くことがある．複数の部品からなる図を作成・編集したら，保存したPPTXを[検査スクリプト](../scripts/pptx_grouping.py)に渡す．禁止設定のある部品が，スライドの表示順・図形ID・名前で分かる．設定の意味は[Microsoftの仕様](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.shapelocks.nogrouping?view=openxml-3.0.1)を参照．

```sh
python scripts/pptx_grouping.py draft.pptx
```

例えば3枚目の図形12・13を依頼者が一緒に動かす場合は，その2点を指定して解除したコピーを作る．見本から受け継いだ保護は用途を確かめて残す．提出するコピーにも検査をかけ，指定した部品が一覧から消えたことを確かめる．

```sh
python scripts/pptx_grouping.py draft.pptx --allow 3:12 3:13 --output editable.pptx
```

**同じ対象を何と呼んでいるか．** [全文抽出・検索](../scripts/find_pptx_text.py)に提出用PPTXだけを渡すと，各ページの図形・表セルの全文を読める．画像の文字やグラフのラベルは表示したページで読む．例えば本文で試験片を `specimen`，図で同じ試験片を `test piece` と呼んでいれば，図のラベルを `specimen` にそろえる．`specimen holder` は支持具の名前として残す．見つかった旧表記は，修正後のファイルで原文と件数を調べられる．

```sh
python scripts/find_pptx_text.py final.pptx
python scripts/find_pptx_text.py final.pptx "test piece"
```

著者が手で直した図形を残して周辺を編集するときは，編集元と保存後のファイルから，位置・経路・塗り・線端などの設定を[比較スクリプト](../scripts/compare_pptx_shape.py)で照合できる．ページは表示順で指定し，選択ウィンドウの名前か `--id` で図形を特定する．

```sh
python scripts/compare_pptx_shape.py before.pptx after.pptx --slide 3 --name "図形 3"
```

差が出た場合は，意図した変更かを元の図形と照らす．見た目はテーマや周囲の図形にも依存するため，表示の比較も行う．
