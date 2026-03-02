# MoneyForward 仕訳自動化 詳細リファレンス

Chrome DevTools MCP（`evaluate_script`）を使った MoneyForward クラウド会計の仕訳操作手順。

---

## UI 構成のポイント

### MoneyForward のポータルコンポーネント

MoneyForward クラウド会計の科目選択 UI は `ca-client-searchable-select` という React ポータルコンポーネントで構成されている。

```
ページ DOM
├── メインコンテンツ
│   └── button.selectedChoiceLabel___uFaxz  ← 科目選択ボタン
└── body 直下（ポータル）
    ├── div[class*="ca-client"]              ← ドロップダウンリスト
    │   └── input（検索フィールド）
    └── div[data-testid*="click-blocker"]   ← ポータル外クリックをブロック
```

**clickBlocker 問題**: ポータルを開いたまま他の操作をしようとすると `clickBlocker` div がクリックを遮断する。`disableBlockers()` で `pointerEvents: none` にして回避する。

### セレクタ一覧

| セレクタ | 説明 |
|----------|------|
| `button.selectedChoiceLabel___uFaxz` | 科目・補助・取引先の選択ボタン |
| `input.hasDatepicker` | 取引日入力（jQuery datepicker 管理） |
| `input[class*="ca-client-bootstrap-reset-css"]` | 金額入力（一覧で8つ = 4行×借方・貸方） |
| `textarea`（メモ欄除く） | 摘要入力（4行分） |
| `[data-testid*="click-blocker"]` | クリックブロッカー |
| `div.ca-client-bootstrap-reset-css`（z-index > 100） | 開いているポータルのコンテナ |
| `div.dropDownListItem___UKnbP`（コンテナ内） | ドロップダウンの各選択肢 |

**重要**: ポータルコンテナの特定には z-index チェックが必須。`getPortalContainer()` を使うこと。単純に `className.includes('ca-client')` だけでは不十分（click-blocker や他の非表示要素も一致するため）。

---

## 仕訳追加の完全手順

### Step 1: ページを開く

```
mcp__chrome-devtools__navigate_page(url="https://accounting.moneyforward.com/journal_entry")
# 3秒待機
```

### Step 2: ヘルパー関数を注入

SKILL.md の「ヘルパー関数」セクションのコードをそのまま `evaluate_script` に渡す。

### Step 3: 日付を設定

```javascript
// evaluate_script で実行
const inp = document.querySelector('input.hasDatepicker');
if (inp && typeof jQuery !== 'undefined') {
  jQuery(inp).datepicker('setDate', new Date(2026, 2, 25)); // 3月25日
  jQuery(inp).trigger('change').trigger('blur');
}
```

**注意**: `datepicker('option', 'dateFormat')` は `"mm/dd"`。年は会計年度（8月〜翌7月）から自動判定される。`new Date(year, month-1, day)` で指定する。

### Step 4: 科目を選択（selectFromPortal を使う）

```javascript
// ヘルパー注入後に実行
await selectFromPortal(1, '未払費用', '未払費用');   // 借方科目（検索テキスト, 選択テキスト）
await selectFromPortal(2, '', '{補助科目名}');        // 借方補助
await selectFromPortal(3, '', '{取引先名}');          // 借方取引先
await selectFromPortal(4, '普通預金', '普通預金');   // 貸方科目
```

**銀行口座（長い名称）の選択**:

```javascript
// evaluate_script で実行（ヘルパー注入後）
// selectFromPortal で searchText を指定するだけでOK（内部で getPortalContainer() を使用）
await selectFromPortal(5, '三井', '【法人】三井住友銀行トランクNORTH支店普通0211465');
// または部分一致で
const result = await (async () => {
  disableBlockers();
  document.querySelectorAll('button.selectedChoiceLabel___uFaxz')[5].click();
  await new Promise(r => setTimeout(r, 800));
  const inp = getPortalInput();
  inp.focus(); document.execCommand('selectAll');
  document.execCommand('insertText', false, '三井');
  await new Promise(r => setTimeout(r, 700));
  return clickPortalItemByKeywords(['三井', 'NORTH'], 80);
})();
// result に選択テキストが返る
```

### Step 5: 金額を設定

```javascript
// 金額フィールドは ca-client-bootstrap-reset-css クラスを含む input[type="text"]
// ※ 取得順: [0]=Row1借方, [1]=Row1貸方, [2]=Row2借方, [3]=Row2貸方 ...
const allInputs = [...document.querySelectorAll('input[type="text"]')].filter(el => el.offsetParent !== null);
const amountInputs = allInputs.filter(inp => inp.className.includes('ca-client-bootstrap-reset-css'));

const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
const setAmount = (inp, val) => {
  inp.focus();
  setter.call(inp, val);
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  inp.blur();
};

setAmount(amountInputs[0], '18610'); // Row1借方
setAmount(amountInputs[1], '18610'); // Row1貸方
```

### Step 6: 摘要を設定

```javascript
const ta = document.querySelector('textarea');
ta.focus();
document.execCommand('selectAll');
document.execCommand('insertText', false, '振替 フリコミ／2026年02月分 役員報酬');
```

### Step 7: 登録ボタンをクリック

```javascript
disableBlockers();
const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '登録');
btn?.click();
```

### Step 8: 確認

`take_screenshot` または `navigate_page` で仕訳リストを再表示して確認。

---

## 既存仕訳の編集手順

### 仕訳リストから対象を探す

```javascript
// evaluate_script で実行
const rows = document.querySelectorAll('table tbody tr');
const results = [];
for (const row of rows) {
  const cells = row.querySelectorAll('td');
  if (cells.length >= 5) {
    results.push({
      no: cells[1]?.textContent?.trim(),
      date: cells[2]?.textContent?.trim(),
      debit: cells[3]?.textContent?.trim()?.slice(0, 30),
      amount: cells[5]?.textContent?.trim(),
      description: cells[9]?.textContent?.trim()?.slice(0, 40),
    });
  }
}
return results.slice(0, 20);
```

### 編集ボタンをクリック

```javascript
// No. で対象行を特定して編集リンクをクリック
const rows = document.querySelectorAll('table tbody tr');
for (const row of rows) {
  const no = row.querySelectorAll('td')[1]?.textContent?.trim();
  if (no === '77') {
    // 編集ボタンを探す（テキスト or アイコン）
    const editBtn = Array.from(row.querySelectorAll('a, button'))
      .find(el => el.textContent.includes('編集') || el.href?.includes('edit'));
    editBtn?.click();
    break;
  }
}
```

### 摘要のみ修正して保存

```javascript
// 編集フォームで摘要を変更
const ta = document.querySelector('textarea');
ta.focus(); document.execCommand('selectAll');
document.execCommand('insertText', false, '正しい摘要テキスト');

// 保存ボタン（編集フォームは「保存」）
disableBlockers();
Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '保存')?.click();
```

---

## 月次バッチスクリプト

### リポジトリ

```
~/path/to/moneyforward-scripts/
├── scripts/
│   ├── helpers.js                    # DOM ヘルパー（Node.js Playwright 用）
│   └── monthly/
│       └── add-payment-journal.js   # 役員報酬支払仕訳スクリプト
```

### 実行方法

```bash
cd ~/path/to/moneyforward-scripts
NODE_PATH="$(pwd)/node_modules" node scripts/monthly/add-payment-journal.js \
  --date MM/DD \
  --description "摘要テキスト" \
  [--amount 18610] \
  [--dry-run]
```

### 毎月25日の実行例

```bash
# 実行前に Chrome を CDP モードで起動済みであること

# 2026年3月分（2026年4月25日実行）
NODE_PATH="$(pwd)/node_modules" node scripts/monthly/add-payment-journal.js \
  --date 04/25 \
  --description "振替 フリコミ／2026年03月分 役員報酬"
```

### 固定値（スクリプト内にハードコード）

- **借方科目**: 未払費用 / {補助科目} / {取引先} （スクリプト内で設定）
- **貸方科目**: 普通預金 / {銀行名・支店名} （スクリプト内で設定）
- **金額**: デフォルト値（`--amount` で変更可）

---

## トラブルシューティング

### clickPortalItem が false を返す

- ポータルが開いていない → 対象ボタンを先にクリック
- 検索結果がない → searchText を変える（例: 「法定福利費」で検索）
- `getPortalContainer()` が null を返す → ドロップダウンが開いていない / z-index が低い
- 誤ったフィールドに入力される → `getPortalContainer()` で z-index チェックを確認

### 入力テキストが別フィールド（タグ欄など）に入ってしまう

- **原因**: ドロップダウンが開いていない状態で `document.activeElement` に入力している
- **解決**: 必ず `btns[btnIndex].click()` → 800ms 待機 → `getPortalContainer()` で確認 → `getPortalInput()` の順に実行する

### 日付が正しく設定されない

- jQuery が未ロードの場合は再試行
- datepicker の `setDate` は月が 0-indexed: `new Date(year, month-1, day)`

### 登録後にエラーが表示される

- 借方・貸方の金額が不一致 → 両方の金額入力を確認
- 必須項目が未入力 → 科目選択ボタンのテキストを確認
