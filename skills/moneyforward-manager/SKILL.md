---
name: moneyforward-manager
description: MoneyForward クラウドひとり法人プランの管理・操作スキル。会計・給与・年末調整・社会保険など各サービスの利用方法案内と、Chrome DevTools MCP 経由での仕訳自動化操作（仕訳追加・編集・確認）を提供。MFクラウド、マネフォ、マネーフォワード、仕訳入力、仕訳追加、仕訳修正、役員報酬、仕訳自動化、MoneyForward操作、クラウド会計関連の質問・操作時に使用。
version: 1.0.0
author: asgr-base
createDate: 2026-03-03
updateDate: 2026-03-03
license: Apache-2.0
---

# MoneyForward Manager

MoneyForward クラウドひとり法人プランの利用ガイド + Chrome DevTools MCP 経由での仕訳自動化。

## 重要: 最新情報の取得

**サービス利用方法・料金・機能制限について回答する際は、必ずWebSearchまたはWebFetchで公式サポートサイトから最新情報を取得してから回答すること。**

---

## Part 1: ひとり法人プラン ガイド

### 概要

| 項目 | 内容 |
|------|------|
| 年払い | 2,480円/月（29,760円/年） |
| 月払い | 3,980円/月 |
| 対象 | 経営者1名のみの法人（従業員なし） |

### 含まれるサービス（全12サービス）

| カテゴリ | サービス |
|---------|----------|
| 経理財務 | 会計、請求書、経費、債務支払 |
| 人事労務 | 給与、勤怠、年末調整、社会保険、マイナンバー、人事管理 |
| その他 | 契約、Box |

### 主な制限事項

| 項目 | ひとり法人 | スモールビジネス |
|------|-----------|-----------------|
| 利用人数 | 1名 | 3名 |
| 年間仕訳数 | 500件 | 無制限 |
| AI-OCR | 30件/月 | 60件/月 |
| 消費税申告書 | 不可 | 可 |

### 情報検索

| 目的 | URL |
|------|-----|
| 会計全般 | https://biz.moneyforward.com/support/account/ |
| 給与計算 | https://biz.moneyforward.com/support/payroll/ |
| 年末調整 | https://biz.moneyforward.com/support/tax-adjustment/ |
| 社会保険 | https://biz.moneyforward.com/support/social-insurance/ |
| 料金プラン | https://biz.moneyforward.com/support/plan/ |

詳細は [REFERENCE.md](REFERENCE.md) を参照。

---

## Part 2: Chrome DevTools MCP 仕訳自動化

### 前提条件

Chrome が CDP デバッグモードで起動済みであること:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile  # 任意のパスに変更可
```

`mcp__chrome-devtools__list_pages` で MoneyForward のタブを確認する。

### アーキテクチャ

```
[アドホック操作]
Claude → mcp__chrome-devtools__evaluate_script → Chrome CDP → MoneyForward

[月次バッチ]
node ~/path/to/moneyforward-scripts/scripts/monthly/add-payment-journal.js
```

### ヘルパー関数（evaluate_script に毎回注入）

```javascript
function disableBlockers() {
  document.querySelectorAll('[data-testid*="click-blocker"], [class*="clickBlocker"]')
    .forEach(el => { el.style.pointerEvents = 'none'; el.style.zIndex = '-999'; });
}
// ドロップダウンのコンテナを取得（z-index > 100 かつ visible なもの）
function getPortalContainer() {
  const children = Array.from(document.body.children);
  for (let i = children.length - 1; i >= 0; i--) {
    const child = children[i];
    if ((child.className || '').includes('ca-client-bootstrap-reset-css') &&
        child.offsetParent !== null &&
        parseInt(window.getComputedStyle(child).zIndex) > 100) {
      return child;
    }
  }
  return null;
}
function getPortalInput() {
  const container = getPortalContainer();
  return container ? container.querySelector('input[type="text"]') : null;
}
function clickPortalItem(text) {
  const container = getPortalContainer();
  if (!container) return false;
  for (const el of container.querySelectorAll('div.dropDownListItem___UKnbP')) {
    if (el.textContent.trim() === text && el.offsetParent !== null) {
      el.click(); return true;
    }
  }
  return false;
}
function clickPortalItemByKeywords(keywords, maxLength = 80) {
  const container = getPortalContainer();
  if (!container) return null;
  for (const el of container.querySelectorAll('div.dropDownListItem___UKnbP')) {
    const t = el.textContent.trim();
    if (t.length < maxLength && keywords.every(k => t.includes(k)) && el.offsetParent !== null) {
      el.click(); return t;
    }
  }
  return null;
}
async function selectFromPortal(btnIndex, searchText, selectText) {
  disableBlockers();
  const btns = document.querySelectorAll('button.selectedChoiceLabel___uFaxz');
  btns[btnIndex].click();
  await new Promise(r => setTimeout(r, 800));
  if (searchText) {
    const inp = getPortalInput();
    if (inp) {
      inp.focus(); document.execCommand('selectAll');
      document.execCommand('insertText', false, searchText);
      await new Promise(r => setTimeout(r, 700));
    }
  }
  const ok = clickPortalItem(selectText);
  await new Promise(r => setTimeout(r, 500));
  return ok;
}
```

### 新規仕訳入力フォームのボタン構造

| インデックス | 項目 |
|-------------|------|
| [0] | 仕訳書（通常「使用しない」） |
| [1] | 借方科目 |
| [2] | 借方補助科目 |
| [3] | 借方取引先 |
| [4] | 貸方科目 |
| [5] | 貸方補助科目 |
| [6] | 貸方取引先 |

### 日付・金額・摘要の設定

```javascript
// 日付（datepicker フォーマットは "mm/dd"、年は会計年度から自動判定）
const inp = document.querySelector('input.hasDatepicker');
jQuery(inp).datepicker('setDate', new Date(2026, 2, 25)); // → "03/25"
jQuery(inp).trigger('change').trigger('blur');

// 金額（React native setter で設定）
const amtInp = document.querySelectorAll('input[class*="ca-client-formattable"]')[0];
const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
setter.call(amtInp, '18610');
['input','change','blur'].forEach(e => amtInp.dispatchEvent(new Event(e, {bubbles:true})));

// 摘要
const ta = document.querySelector('textarea');
ta.focus(); document.execCommand('selectAll');
document.execCommand('insertText', false, '{摘要テキスト}');  // 例: '振替 フリコミ／2026年02月分 役員報酬'

// 登録ボタン
Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '登録')?.click();
```

### 月次バッチ（役員報酬支払）

```bash
# ~/path/to/moneyforward-scripts は実際のパスに変更すること
cd ~/path/to/moneyforward-scripts
NODE_PATH="$(pwd)/node_modules" node scripts/monthly/add-payment-journal.js \
  --date MM/DD \
  --description "摘要テキスト"
```

詳細な手順は [references/automation.md](references/automation.md) を参照。
