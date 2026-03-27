#!/usr/bin/env python3
"""
aoiro.py - 青色申告帳簿作成CLI

Markdownテーブル形式の仕訳帳から帳簿・決算書を自動生成する。
Python標準ライブラリのみ使用（追加パッケージ不要）。

準拠法令:
    - 所得税法 第148条, 第149条（帳簿書類の備付け・決算書添付）
    - 租税特別措置法 第25条の2（青色申告特別控除）
    - 所得税法施行令 第129条（定額法）, 第130条（定率法）
    - 所得税法施行令 第135条（非業務用資産の転用）
    - 減価償却資産の耐用年数等に関する省令（耐用年数・償却率）

Usage:
    python3 aoiro.py validate <仕訳帳.md>
    python3 aoiro.py generate <仕訳帳.md> --output-dir <出力先>
    python3 aoiro.py settlement <仕訳帳.md> --output-dir <出力先>
    python3 aoiro.py depreciation <固定資産台帳.md> --year <年>
    python3 aoiro.py allocation <仕訳帳.md> --config <家事按分設定.md>
    python3 aoiro.py init --year <年> --output-dir <出力先>
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple


# =============================================================================
# Data types
# =============================================================================

class JournalEntry(NamedTuple):
    """仕訳1行"""
    line_num: int
    date: str
    debit_account: str
    debit_amount: int
    credit_account: str
    credit_amount: int
    description: str


class AccountMaster(NamedTuple):
    """科目マスタ1行"""
    name: str
    balance_type: str   # 借方 or 貸方
    display_order: int
    statement_type: str  # 損益計算書 or 貸借対照表
    note: str


class FixedAsset(NamedTuple):
    """固定資産1行"""
    name: str
    acquisition_date: str
    acquisition_cost: int
    method: str          # 定額法 or 定率法
    useful_life: int
    depreciation_rate: float
    business_ratio: float  # 0-100
    business_start_date: str
    transfer_balance: int  # 転用時残高 (0 = 新規取得)
    note: str


class AllocationConfig(NamedTuple):
    """家事按分設定1行"""
    account: str
    ratio: int  # 事業使用割合 0-100
    reason: str


# =============================================================================
# Markdown table parser
# =============================================================================

def parse_amount(s: str) -> int:
    """金額文字列を整数に変換。カンマ除去。空文字列は0。"""
    s = s.strip()
    if not s:
        return 0
    return int(s.replace(",", ""))


def format_amount(n: int) -> str:
    """整数をカンマ区切り文字列に変換。"""
    return f"{n:,}"


def parse_markdown_table(text: str) -> List[List[str]]:
    """Markdownテーブルをパースし、行のリストを返す。

    ヘッダー行とセパレーター行（|---|）はスキップする。
    """
    rows = []
    lines = text.strip().split("\n")
    header_found = False
    separator_found = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue

        # セルを抽出
        cells = [c.strip() for c in line.split("|")]
        # 先頭と末尾の空文字列を除去（| で始まり | で終わるため）
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if not cells:
            continue

        # セパレーター行の検出（全セルが --- パターン）
        if all(re.match(r"^[-:]+$", c) for c in cells):
            separator_found = True
            continue

        if not header_found:
            header_found = True
            continue  # ヘッダー行スキップ

        if separator_found:
            rows.append(cells)

    return rows


def parse_journal(file_path: Path) -> Tuple[List[JournalEntry], Dict[str, str]]:
    """仕訳帳Markdownをパースし、仕訳リストと設定を返す。"""
    text = file_path.read_text(encoding="utf-8")
    entries = []
    config = {}

    # 設定セクションのパース
    config_match = re.search(r"## 設定\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if config_match:
        for line in config_match.group(1).split("\n"):
            m = re.match(r"-\s*(.+?):\s*(.+)", line.strip())
            if m:
                config[m.group(1).strip()] = m.group(2).strip()

    # 仕訳データセクションのパース
    data_match = re.search(r"## 仕訳データ\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if not data_match:
        return entries, config

    # テーブルのある部分のテキストを取得
    table_text = data_match.group(1)
    table_lines = table_text.strip().split("\n")

    # 行番号を追跡するため、元テキストでの行番号を計算
    all_lines = text.split("\n")
    data_section_start = text[:data_match.start()].count("\n")

    rows = []
    header_found = False
    separator_found = False
    line_offset = 0

    for i, line in enumerate(table_lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [c.strip() for c in stripped.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if not cells:
            continue

        if all(re.match(r"^[-:]+$", c) for c in cells):
            separator_found = True
            continue

        if not header_found:
            header_found = True
            continue

        if separator_found:
            # 元ファイルでの行番号（1-indexed）
            actual_line = data_section_start + i + 2
            rows.append((actual_line, cells))

    for line_num, cells in rows:
        if len(cells) < 6:
            # 不足分を空文字で埋める
            cells.extend([""] * (6 - len(cells)))

        try:
            entry = JournalEntry(
                line_num=line_num,
                date=cells[0].strip(),
                debit_account=cells[1].strip(),
                debit_amount=parse_amount(cells[2]),
                credit_account=cells[3].strip(),
                credit_amount=parse_amount(cells[4]),
                description=cells[5].strip(),
            )
            entries.append(entry)
        except (ValueError, IndexError) as e:
            print(f"WARNING: 行{line_num}のパースに失敗: {e}", file=sys.stderr)

    return entries, config


def parse_account_master(file_path: Path) -> List[AccountMaster]:
    """科目マスタをパースする。複数テーブル対応。"""
    text = file_path.read_text(encoding="utf-8")
    accounts = []

    # テーブルを含むセクションを全て探す
    rows = parse_markdown_table(text)

    for cells in rows:
        if len(cells) < 5:
            continue
        try:
            accounts.append(AccountMaster(
                name=cells[0].strip(),
                balance_type=cells[1].strip(),
                display_order=int(cells[2].strip()),
                statement_type=cells[3].strip(),
                note=cells[4].strip(),
            ))
        except (ValueError, IndexError):
            continue

    return accounts


def parse_fixed_assets(file_path: Path) -> List[FixedAsset]:
    """固定資産台帳をパースする。"""
    text = file_path.read_text(encoding="utf-8")
    assets = []

    rows = parse_markdown_table(text)

    for cells in rows:
        if len(cells) < 10:
            cells.extend([""] * (10 - len(cells)))
        try:
            assets.append(FixedAsset(
                name=cells[0].strip(),
                acquisition_date=cells[1].strip(),
                acquisition_cost=parse_amount(cells[2]),
                method=cells[3].strip(),
                useful_life=int(cells[4].strip()) if cells[4].strip() else 0,
                depreciation_rate=float(cells[5].strip()) if cells[5].strip() else 0.0,
                business_ratio=float(cells[6].strip()) if cells[6].strip() else 100.0,
                business_start_date=cells[7].strip(),
                transfer_balance=parse_amount(cells[8]),
                note=cells[9].strip(),
            ))
        except (ValueError, IndexError):
            continue

    return assets


def parse_allocation_config(file_path: Path) -> List[AllocationConfig]:
    """家事按分設定をパースする。"""
    text = file_path.read_text(encoding="utf-8")
    configs = []

    # 「按分設定」セクション内のテーブルのみパース
    section_match = re.search(r"## 按分設定\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if not section_match:
        # セクションがなければ全体をパース
        section_text = text
    else:
        section_text = section_match.group(1)

    rows = parse_markdown_table(section_text)

    for cells in rows:
        if len(cells) < 3:
            continue
        try:
            configs.append(AllocationConfig(
                account=cells[0].strip(),
                ratio=int(cells[1].strip()),
                reason=cells[2].strip(),
            ))
        except (ValueError, IndexError):
            continue

    return configs


def resolve_account_master(journal_path: Path, config: dict) -> Optional[Path]:
    """仕訳帳の設定から科目マスタのパスを解決する。"""
    master_ref = config.get("科目マスタ", "科目マスタ.md")
    master_path = (journal_path.parent / master_ref).resolve()
    if master_path.exists():
        return master_path
    return None


# =============================================================================
# validate subcommand
# =============================================================================

def cmd_validate(args: argparse.Namespace) -> int:
    """仕訳帳のバリデーション。"""
    journal_path = Path(args.journal)
    if not journal_path.exists():
        print(f"ERROR: ファイルが見つかりません: {journal_path}", file=sys.stderr)
        return 1

    entries, config = parse_journal(journal_path)
    if not entries:
        print(f"WARNING: 仕訳データが見つかりません: {journal_path}")
        return 0

    # 科目マスタの読み込み
    master_path = resolve_account_master(journal_path, config)
    account_names = set()
    if master_path:
        accounts = parse_account_master(master_path)
        account_names = {a.name for a in accounts}
    else:
        print(f"WARNING: 科目マスタが見つかりません。科目チェックをスキップします。")

    errors = []
    warnings = []

    for entry in entries:
        # 日付チェック
        try:
            datetime.strptime(entry.date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"行{entry.line_num}: 日付の形式が不正です: '{entry.date}' (YYYY-MM-DD形式で入力)")

        # 貸借一致チェック
        if entry.debit_amount != entry.credit_amount:
            errors.append(
                f"行{entry.line_num}: 貸借不一致 借方={format_amount(entry.debit_amount)} "
                f"貸方={format_amount(entry.credit_amount)} 差額={format_amount(entry.debit_amount - entry.credit_amount)}"
            )

        # 金額ゼロチェック
        if entry.debit_amount == 0 and entry.credit_amount == 0:
            warnings.append(f"行{entry.line_num}: 金額がゼロです")

        # 科目存在チェック
        if account_names:
            if entry.debit_account and entry.debit_account not in account_names:
                errors.append(f"行{entry.line_num}: 借方科目が科目マスタに存在しません: '{entry.debit_account}'")
            if entry.credit_account and entry.credit_account not in account_names:
                errors.append(f"行{entry.line_num}: 貸方科目が科目マスタに存在しません: '{entry.credit_account}'")

        # 摘要の空チェック
        if not entry.description:
            warnings.append(f"行{entry.line_num}: 摘要が空です")

    # 期間チェック
    period = config.get("期間", "")
    if period:
        parts = period.split("〜")
        if len(parts) == 2:
            try:
                start = datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
                end = datetime.strptime(parts[1].strip(), "%Y-%m-%d").date()
                for entry in entries:
                    try:
                        d = datetime.strptime(entry.date, "%Y-%m-%d").date()
                        if d < start or d > end:
                            warnings.append(
                                f"行{entry.line_num}: 日付 {entry.date} が期間外です "
                                f"({start.isoformat()} 〜 {end.isoformat()})"
                            )
                    except ValueError:
                        pass  # 日付形式エラーは上で報告済み
            except ValueError:
                pass

    # 結果出力
    print(f"=== バリデーション結果 ===")
    print(f"ファイル: {journal_path}")
    print(f"仕訳件数: {len(entries)}件")

    if errors:
        print(f"\nERROR: {len(errors)}件")
        for e in errors:
            print(f"  {e}")

    if warnings:
        print(f"\nWARNING: {len(warnings)}件")
        for w in warnings:
            print(f"  {w}")

    if not errors and not warnings:
        print("\nOK: エラーなし")

    # 集計サマリー
    total_debit = sum(e.debit_amount for e in entries)
    total_credit = sum(e.credit_amount for e in entries)
    print(f"\n借方合計: {format_amount(total_debit)}")
    print(f"貸方合計: {format_amount(total_credit)}")

    return 1 if errors else 0


# =============================================================================
# generate subcommand
# =============================================================================

def cmd_generate(args: argparse.Namespace) -> int:
    """総勘定元帳・残高試算表の生成。"""
    journal_path = Path(args.journal)
    output_dir = Path(args.output_dir)

    if not journal_path.exists():
        print(f"ERROR: ファイルが見つかりません: {journal_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    entries, config = parse_journal(journal_path)
    if not entries:
        print("WARNING: 仕訳データが見つかりません。")
        return 0

    # 科目マスタ読み込み
    master_path = resolve_account_master(journal_path, config)
    accounts_map = {}  # type: Dict[str, AccountMaster]
    if master_path:
        for a in parse_account_master(master_path):
            accounts_map[a.name] = a

    # --- 総勘定元帳 ---
    # 科目ごとに仕訳を集計
    ledger = defaultdict(list)  # type: Dict[str, List[dict]]

    for entry in entries:
        if entry.debit_account:
            ledger[entry.debit_account].append({
                "date": entry.date,
                "counterpart": entry.credit_account,
                "description": entry.description,
                "debit": entry.debit_amount,
                "credit": 0,
            })
        if entry.credit_account:
            ledger[entry.credit_account].append({
                "date": entry.date,
                "counterpart": entry.debit_account,
                "description": entry.description,
                "debit": 0,
                "credit": entry.credit_amount,
            })

    # 科目の表示順でソート
    def sort_key(account_name: str) -> tuple:
        if account_name in accounts_map:
            a = accounts_map[account_name]
            type_order = 0 if a.statement_type == "損益計算書" else 1
            return (type_order, a.display_order)
        return (999, 999)

    sorted_accounts = sorted(ledger.keys(), key=sort_key)

    # 総勘定元帳の生成
    lines = ["# 総勘定元帳\n"]
    period = config.get("期間", "")
    if period:
        lines.append(f"期間: {period}\n")
    lines.append("")

    for account_name in sorted_accounts:
        records = sorted(ledger[account_name], key=lambda r: r["date"])
        balance_type = "借方"
        if account_name in accounts_map:
            balance_type = accounts_map[account_name].balance_type

        lines.append(f"## {account_name}\n")
        lines.append("| 日付 | 相手科目 | 摘要 | 借方金額 | 貸方金額 | 残高 |")
        lines.append("|------|---------|------|---------|---------|------|")

        running_balance = 0
        for r in records:
            if balance_type == "借方":
                running_balance += r["debit"] - r["credit"]
            else:
                running_balance += r["credit"] - r["debit"]

            lines.append(
                f"| {r['date']} | {r['counterpart']} | {r['description']} "
                f"| {format_amount(r['debit']) if r['debit'] else ''} "
                f"| {format_amount(r['credit']) if r['credit'] else ''} "
                f"| {format_amount(running_balance)} |"
            )

        debit_total = sum(r["debit"] for r in records)
        credit_total = sum(r["credit"] for r in records)
        lines.append(
            f"| | | **合計** | **{format_amount(debit_total)}** "
            f"| **{format_amount(credit_total)}** | **{format_amount(running_balance)}** |"
        )
        lines.append("")

    ledger_path = output_dir / "総勘定元帳.md"
    ledger_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"総勘定元帳を生成: {ledger_path}")

    # --- 残高試算表 ---
    lines = ["# 残高試算表\n"]
    if period:
        lines.append(f"期間: {period}\n")
    lines.append("")
    lines.append("| 科目名 | 借方合計 | 貸方合計 | 借方残高 | 貸方残高 |")
    lines.append("|--------|---------|---------|---------|---------|")

    grand_debit_total = 0
    grand_credit_total = 0
    grand_debit_balance = 0
    grand_credit_balance = 0

    for account_name in sorted_accounts:
        records = ledger[account_name]
        debit_total = sum(r["debit"] for r in records)
        credit_total = sum(r["credit"] for r in records)

        balance_type = "借方"
        if account_name in accounts_map:
            balance_type = accounts_map[account_name].balance_type

        if balance_type == "借方":
            net = debit_total - credit_total
            debit_balance = net if net > 0 else 0
            credit_balance = -net if net < 0 else 0
        else:
            net = credit_total - debit_total
            debit_balance = -net if net < 0 else 0
            credit_balance = net if net > 0 else 0

        grand_debit_total += debit_total
        grand_credit_total += credit_total
        grand_debit_balance += debit_balance
        grand_credit_balance += credit_balance

        lines.append(
            f"| {account_name} "
            f"| {format_amount(debit_total)} "
            f"| {format_amount(credit_total)} "
            f"| {format_amount(debit_balance) if debit_balance else ''} "
            f"| {format_amount(credit_balance) if credit_balance else ''} |"
        )

    lines.append(
        f"| **合計** "
        f"| **{format_amount(grand_debit_total)}** "
        f"| **{format_amount(grand_credit_total)}** "
        f"| **{format_amount(grand_debit_balance)}** "
        f"| **{format_amount(grand_credit_balance)}** |"
    )

    trial_path = output_dir / "残高試算表.md"
    trial_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"残高試算表を生成: {trial_path}")

    return 0


# =============================================================================
# settlement subcommand
# =============================================================================

def cmd_settlement(args: argparse.Namespace) -> int:
    """損益計算書・貸借対照表の生成。"""
    journal_path = Path(args.journal)
    output_dir = Path(args.output_dir)

    if not journal_path.exists():
        print(f"ERROR: ファイルが見つかりません: {journal_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    entries, config = parse_journal(journal_path)
    if not entries:
        print("WARNING: 仕訳データが見つかりません。")
        return 0

    # 科目マスタ読み込み
    master_path = resolve_account_master(journal_path, config)
    accounts_map = {}  # type: Dict[str, AccountMaster]
    if master_path:
        for a in parse_account_master(master_path):
            accounts_map[a.name] = a

    # 科目ごとの集計
    debit_totals = defaultdict(int)  # type: Dict[str, int]
    credit_totals = defaultdict(int)  # type: Dict[str, int]

    for entry in entries:
        if entry.debit_account:
            debit_totals[entry.debit_account] += entry.debit_amount
        if entry.credit_account:
            credit_totals[entry.credit_account] += entry.credit_amount

    # 全科目
    all_accounts = set(debit_totals.keys()) | set(credit_totals.keys())

    # 科目残高の計算
    def get_balance(name: str) -> int:
        """科目の残高を返す（自然な方向で正の値）。"""
        bt = "借方"
        if name in accounts_map:
            bt = accounts_map[name].balance_type
        if bt == "借方":
            return debit_totals.get(name, 0) - credit_totals.get(name, 0)
        else:
            return credit_totals.get(name, 0) - debit_totals.get(name, 0)

    # --- 損益計算書 ---
    pl_accounts = [
        a for a in accounts_map.values()
        if a.statement_type == "損益計算書"
    ]
    pl_accounts.sort(key=lambda a: a.display_order)

    revenue_accounts = [a for a in pl_accounts if a.balance_type == "貸方"]
    expense_accounts = [a for a in pl_accounts if a.balance_type == "借方"]

    lines = ["# 損益計算書\n"]
    period = config.get("期間", "")
    if period:
        lines.append(f"期間: {period}\n")
    lines.append("")

    # 収入の部
    lines.append("## 収入の部\n")
    lines.append("| 科目 | 金額 |")
    lines.append("|------|------|")
    total_revenue = 0
    for a in revenue_accounts:
        bal = get_balance(a.name)
        if bal != 0 or a.name in all_accounts:
            lines.append(f"| {a.name} | {format_amount(bal)} |")
            total_revenue += bal
    lines.append(f"| **収入合計** | **{format_amount(total_revenue)}** |")
    lines.append("")

    # 経費の部
    lines.append("## 経費の部\n")
    lines.append("| 科目 | 金額 |")
    lines.append("|------|------|")
    total_expense = 0
    for a in expense_accounts:
        bal = get_balance(a.name)
        if bal != 0:
            lines.append(f"| {a.name} | {format_amount(bal)} |")
            total_expense += bal
    lines.append(f"| **経費合計** | **{format_amount(total_expense)}** |")
    lines.append("")

    # 差引金額
    net_income = total_revenue - total_expense
    lines.append("## 所得金額\n")
    lines.append("| 項目 | 金額 |")
    lines.append("|------|------|")
    lines.append(f"| 収入合計 | {format_amount(total_revenue)} |")
    lines.append(f"| 経費合計 | {format_amount(total_expense)} |")
    lines.append(f"| **差引金額（青色申告特別控除前）** | **{format_amount(net_income)}** |")
    lines.append("")

    pl_path = output_dir / "損益計算書.md"
    pl_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"損益計算書を生成: {pl_path}")

    # --- 貸借対照表 ---
    bs_accounts = [
        a for a in accounts_map.values()
        if a.statement_type == "貸借対照表"
    ]
    bs_accounts.sort(key=lambda a: a.display_order)

    # 青色申告決算書の貸借対照表構成:
    # 左辺: 資産の部 + 事業主貸
    # 右辺: 負債の部 + 事業主借 + 元入金 + 控除前所得
    capital_names = {"事業主借", "事業主貸", "元入金"}
    asset_accounts = [a for a in bs_accounts if a.balance_type == "借方" and a.name not in capital_names]
    liability_accounts = [a for a in bs_accounts if a.balance_type == "貸方" and a.name not in capital_names]

    lines = ["# 貸借対照表\n"]
    if period:
        lines.append(f"期間: {period}\n")
    lines.append("")

    # 資産の部
    lines.append("## 資産の部\n")
    lines.append("| 科目 | 期末残高 |")
    lines.append("|------|---------|")
    total_assets = 0
    for a in asset_accounts:
        bal = get_balance(a.name)
        if bal != 0 or a.name in all_accounts:
            lines.append(f"| {a.name} | {format_amount(bal)} |")
            total_assets += bal
    lines.append(f"| **資産合計** | **{format_amount(total_assets)}** |")
    lines.append("")

    # 負債の部
    lines.append("## 負債の部\n")
    lines.append("| 科目 | 期末残高 |")
    lines.append("|------|---------|")
    total_liabilities = 0
    for a in liability_accounts:
        bal = get_balance(a.name)
        if bal != 0 or a.name in all_accounts:
            lines.append(f"| {a.name} | {format_amount(bal)} |")
            total_liabilities += bal
    lines.append(f"| **負債合計** | **{format_amount(total_liabilities)}** |")
    lines.append("")

    # 資本の部（事業主貸・事業主借・元入金・控除前所得）
    jigyounushi_kari = get_balance("事業主借") if "事業主借" in all_accounts else 0
    jigyounushi_kashi = get_balance("事業主貸") if "事業主貸" in all_accounts else 0
    motoirekin = get_balance("元入金") if "元入金" in all_accounts else 0

    lines.append("## 資本の部\n")
    lines.append("| 科目 | 期末残高 |")
    lines.append("|------|---------|")
    if "事業主貸" in all_accounts:
        lines.append(f"| 事業主貸 | {format_amount(jigyounushi_kashi)} |")
    if "事業主借" in all_accounts:
        lines.append(f"| 事業主借 | {format_amount(jigyounushi_kari)} |")
    lines.append(f"| 元入金 | {format_amount(motoirekin)} |")
    lines.append(f"| 青色申告特別控除前の所得金額 | {format_amount(net_income)} |")
    lines.append("")

    # 貸借一致の検証
    # 左辺: 資産 + 事業主貸 = 右辺: 負債 + 事業主借 + 元入金 + 控除前所得
    left_side = total_assets + jigyounushi_kashi
    right_side = total_liabilities + jigyounushi_kari + motoirekin + net_income
    lines.append("## 貸借検証\n")
    lines.append("| 項目 | 金額 |")
    lines.append("|------|------|")
    lines.append(f"| 資産合計 + 事業主貸（左辺） | {format_amount(left_side)} |")
    lines.append(f"| 負債 + 事業主借 + 元入金 + 所得（右辺） | {format_amount(right_side)} |")
    if left_side == right_side:
        lines.append(f"| **結果** | **OK（一致）** |")
    else:
        diff = left_side - right_side
        lines.append(f"| **結果** | **NG（差額: {format_amount(diff)}）** |")

    bs_path = output_dir / "貸借対照表.md"
    bs_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"貸借対照表を生成: {bs_path}")

    return 0


# =============================================================================
# depreciation subcommand
# =============================================================================

def cmd_depreciation(args: argparse.Namespace) -> int:
    """減価償却費の計算。決算仕訳をMarkdown形式で出力。"""
    asset_path = Path(args.asset_ledger)
    year = args.year

    if not asset_path.exists():
        print(f"ERROR: ファイルが見つかりません: {asset_path}", file=sys.stderr)
        return 1

    assets = parse_fixed_assets(asset_path)
    if not assets:
        print("WARNING: 固定資産データが見つかりません。")
        return 0

    year_end = date(year, 12, 31)
    year_start = date(year, 1, 1)

    print(f"=== {year}年 減価償却費計算 ===\n")

    journal_lines = []
    journal_lines.append("| 日付 | 借方科目 | 借方金額 | 貸方科目 | 貸方金額 | 摘要 |")
    journal_lines.append("|------|---------|---------|---------|---------|------|")

    total_depreciation = 0

    for asset in assets:
        # 事業開始日の決定
        if asset.business_start_date:
            try:
                biz_start = datetime.strptime(asset.business_start_date, "%Y-%m-%d").date()
            except ValueError:
                print(f"WARNING: {asset.name} の事業開始日が不正です: {asset.business_start_date}")
                continue
        else:
            try:
                biz_start = datetime.strptime(asset.acquisition_date, "%Y-%m-%d").date()
            except ValueError:
                print(f"WARNING: {asset.name} の取得日が不正です: {asset.acquisition_date}")
                continue

        # 当年に事業供用していない資産はスキップ
        if biz_start > year_end:
            continue

        # 事業供用月数の計算
        if biz_start.year == year:
            # 当年から事業供用開始
            months = 12 - biz_start.month + 1
        elif biz_start.year < year:
            months = 12
        else:
            continue

        # 年間償却額の計算
        # 定額法（所得税法施行令 第129条）: 取得価額 × 償却率
        # ※平成19年4月1日以後取得の資産に適用。転用資産も取得価額ベース。
        if asset.method == "定額法":
            annual_depreciation = int(asset.acquisition_cost * asset.depreciation_rate)
        elif asset.method == "定率法":
            # 定率法（所得税法施行令 第130条）は累積償却額が必要なため、ここでは簡易計算
            # （正確な計算には過去の償却額情報が必要）
            annual_depreciation = int(asset.acquisition_cost * asset.depreciation_rate)
        else:
            print(f"WARNING: {asset.name} の償却方法が不正です: {asset.method}")
            continue

        # 月割り
        month_depreciation = int(annual_depreciation * months / 12)

        # 事業専用割合（四捨五入で端数処理）
        business_depreciation = round(month_depreciation * asset.business_ratio / 100)
        private_depreciation = month_depreciation - business_depreciation

        # 転用資産の場合、転用時残高を超えて償却しないよう制限
        # （所得税法施行令 第135条。複数年の累積チェックは将来対応）

        if business_depreciation <= 0:
            continue

        total_depreciation += business_depreciation

        # 勘定科目の決定
        # 建物は「建物」、それ以外は「工具器具備品」
        credit_account = "工具器具備品"
        if "建物" in asset.name:
            credit_account = "建物"

        method_label = asset.method
        year_label = f"R{year - 2018}年分" if year >= 2019 else f"{year}年分"

        # 事業分の仕訳（減価償却費 → 資産科目）
        journal_lines.append(
            f"| {year}-12-31 | 減価償却費 | {format_amount(business_depreciation)} "
            f"| {credit_account} | {format_amount(business_depreciation)} "
            f"| {asset.name} {method_label} {year_label}（事業分） |"
        )

        # 私用分の仕訳（事業主貸 → 資産科目）
        if private_depreciation > 0:
            journal_lines.append(
                f"| {year}-12-31 | 事業主貸 | {format_amount(private_depreciation)} "
                f"| {credit_account} | {format_amount(private_depreciation)} "
                f"| {asset.name} {method_label} {year_label}（私用分） |"
            )

        # 明細出力
        print(f"【{asset.name}】")
        print(f"  取得価額: {format_amount(asset.acquisition_cost)}")
        if asset.transfer_balance > 0:
            print(f"  転用時残高: {format_amount(asset.transfer_balance)}")
        print(f"  償却率: {asset.depreciation_rate}")
        print(f"  年間償却額: {format_amount(annual_depreciation)}")
        print(f"  事業月数: {months}ヶ月")
        print(f"  月割り額: {format_amount(month_depreciation)}")
        print(f"  事業専用割合: {asset.business_ratio}%")
        print(f"  当年償却費（事業分）: {format_amount(business_depreciation)}")
        if private_depreciation > 0:
            print(f"  当年償却費（私用分）: {format_amount(private_depreciation)}")
        print()

    print(f"合計減価償却費: {format_amount(total_depreciation)}")
    print()
    print("--- 以下の決算仕訳を仕訳帳に追記してください ---\n")
    print("\n".join(journal_lines))

    return 0


# =============================================================================
# allocation subcommand
# =============================================================================

def cmd_allocation(args: argparse.Namespace) -> int:
    """家事按分仕訳の生成。"""
    journal_path = Path(args.journal)
    config_path = Path(args.config)

    if not journal_path.exists():
        print(f"ERROR: ファイルが見つかりません: {journal_path}", file=sys.stderr)
        return 1
    if not config_path.exists():
        print(f"ERROR: ファイルが見つかりません: {config_path}", file=sys.stderr)
        return 1

    entries, j_config = parse_journal(journal_path)
    alloc_configs = parse_allocation_config(config_path)

    if not alloc_configs:
        print("WARNING: 家事按分設定が見つかりません。")
        return 0

    # 科目ごとの借方合計を計算（既存の按分仕訳を除外）
    account_totals = defaultdict(int)  # type: Dict[str, int]
    for entry in entries:
        # 家事按分の決算仕訳は除外（摘要に「家事按分」を含む）
        if "家事按分" in entry.description:
            continue
        if entry.debit_account:
            account_totals[entry.debit_account] += entry.debit_amount

    # 期末日の決定
    period = j_config.get("期間", "")
    year_end = "12-31"
    if period:
        parts = period.split("〜")
        if len(parts) == 2:
            year_end_str = parts[1].strip()
            try:
                year_end_date = datetime.strptime(year_end_str, "%Y-%m-%d").date()
                year_end = year_end_str
            except ValueError:
                # 年度末のデフォルト
                year_end = f"{datetime.now().year}-12-31"

    print(f"=== 家事按分計算 ===\n")

    journal_lines = []
    journal_lines.append("| 日付 | 借方科目 | 借方金額 | 貸方科目 | 貸方金額 | 摘要 |")
    journal_lines.append("|------|---------|---------|---------|---------|------|")

    total_private = 0

    for ac in alloc_configs:
        total = account_totals.get(ac.account, 0)
        if total == 0:
            print(f"【{ac.account}】経費なし（スキップ）")
            continue

        # 私用分 = 合計 × (100 - 事業割合) / 100
        private_amount = int(total * (100 - ac.ratio) / 100)

        if private_amount <= 0:
            continue

        total_private += private_amount

        journal_lines.append(
            f"| {year_end} | 事業主貸 | {format_amount(private_amount)} "
            f"| {ac.account} | {format_amount(private_amount)} "
            f"| 家事按分 {100 - ac.ratio}%（私用分） |"
        )

        print(f"【{ac.account}】")
        print(f"  年間合計: {format_amount(total)}")
        print(f"  事業割合: {ac.ratio}%")
        print(f"  私用分: {format_amount(private_amount)}（{100 - ac.ratio}%）")
        print(f"  事業分: {format_amount(total - private_amount)}（{ac.ratio}%）")
        print()

    print(f"私用分合計（事業主貸）: {format_amount(total_private)}")
    print()
    print("--- 以下の決算仕訳を仕訳帳に追記してください ---\n")
    print("\n".join(journal_lines))

    return 0


# =============================================================================
# init subcommand
# =============================================================================

def cmd_init(args: argparse.Namespace) -> int:
    """テンプレートから新年度フォルダを作成。"""
    year = args.year
    output_dir = Path(args.output_dir)

    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"WARNING: 出力先にファイルが存在します: {output_dir}")
        print("既存ファイルを上書きしません。空のディレクトリを指定してください。")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    # テンプレートディレクトリの検出
    script_dir = Path(__file__).resolve().parent
    template_dir = script_dir.parent / "templates"

    if not template_dir.exists():
        print(f"ERROR: テンプレートディレクトリが見つかりません: {template_dir}", file=sys.stderr)
        return 1

    # テンプレート変数
    replacements = {
        "{{YEAR}}": str(year),
        "{{START_DATE}}": f"{year}-01-01",
        "{{END_DATE}}": f"{year}-12-31",
    }

    # テンプレートファイルのコピーと変数置換
    copied = []
    for template_file in template_dir.glob("*.md"):
        content = template_file.read_text(encoding="utf-8")
        for key, value in replacements.items():
            content = content.replace(key, value)

        dest = output_dir / template_file.name
        dest.write_text(content, encoding="utf-8")
        copied.append(template_file.name)

    # outputサブディレクトリ作成
    (output_dir / "output").mkdir(exist_ok=True)

    print(f"=== {year}年度の会計データを初期化しました ===\n")
    print(f"出力先: {output_dir}")
    for f in sorted(copied):
        print(f"  {f}")
    print(f"  output/ (帳簿出力先)")
    print()
    print("次のステップ:")
    print("  1. 科目マスタ.md を必要に応じてカスタマイズ")
    print("  2. 仕訳帳.md の設定セクション（期間）を調整")
    print("  3. 仕訳帳.md に仕訳を入力開始")

    return 0


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="aoiro.py - 青色申告帳簿作成CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # validate
    p_validate = subparsers.add_parser("validate", help="仕訳帳のバリデーション")
    p_validate.add_argument("journal", help="仕訳帳Markdownファイルのパス")

    # generate
    p_generate = subparsers.add_parser("generate", help="総勘定元帳・残高試算表の生成")
    p_generate.add_argument("journal", help="仕訳帳Markdownファイルのパス")
    p_generate.add_argument("--output-dir", required=True, help="出力ディレクトリ")

    # settlement
    p_settlement = subparsers.add_parser("settlement", help="損益計算書・貸借対照表の生成")
    p_settlement.add_argument("journal", help="仕訳帳Markdownファイルのパス")
    p_settlement.add_argument("--output-dir", required=True, help="出力ディレクトリ")

    # depreciation
    p_depreciation = subparsers.add_parser("depreciation", help="減価償却費の計算")
    p_depreciation.add_argument("asset_ledger", help="固定資産台帳Markdownファイルのパス")
    p_depreciation.add_argument("--year", type=int, required=True, help="対象年度")

    # allocation
    p_allocation = subparsers.add_parser("allocation", help="家事按分仕訳の生成")
    p_allocation.add_argument("journal", help="仕訳帳Markdownファイルのパス")
    p_allocation.add_argument("--config", required=True, help="家事按分設定ファイルのパス")

    # init
    p_init = subparsers.add_parser("init", help="テンプレートから新年度フォルダを作成")
    p_init.add_argument("--year", type=int, required=True, help="会計年度")
    p_init.add_argument("--output-dir", required=True, help="出力ディレクトリ")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "validate": cmd_validate,
        "generate": cmd_generate,
        "settlement": cmd_settlement,
        "depreciation": cmd_depreciation,
        "allocation": cmd_allocation,
        "init": cmd_init,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
