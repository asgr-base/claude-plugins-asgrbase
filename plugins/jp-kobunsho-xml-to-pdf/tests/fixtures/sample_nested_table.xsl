<?xml version="1.0" encoding="UTF-8"?>
<!-- e-Gov 公文書 XSL の典型構造を模した合成 fixture。
     入れ子 table + 固定 col 幅 + pre.normal(word-wrap) という、
     v2 (WeasyPrint/意味抽出) が崩していたパターンの回帰テスト用。
     データはすべて架空（サンプル太郎）。 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/標準報酬決定通知書">
    <html>
      <head>
        <style>
          .title { font-size: 12pt; text-align: center; }
          .normalTL { font-size: 8pt; vertical-align: top; text-align: left; }
          pre.normal { word-wrap: break-word; }
          table.waku { border-collapse: collapse; }
          table.waku td { border: 1px solid #000; font-size: 8pt; }
        </style>
      </head>
      <body>
        <table width="700">
          <tr><td class="title">健康保険・厚生年金保険被保険者標準報酬決定通知書（テスト様式）</td></tr>
          <tr><td>
            <!-- 入れ子 table -->
            <table class="waku" width="680">
              <colgroup>
                <col width="60"/><col width="180"/><col width="80"/>
                <col width="90"/><col width="90"/><col width="110"/><col width="70"/>
              </colgroup>
              <tr>
                <td>整理番号</td><td>被保険者氏名</td><td>適用年月</td>
                <td>（健保）</td><td>（厚年）</td><td>生年月日</td><td>種別</td>
              </tr>
              <tr>
                <td><xsl:value-of select="被保険者/整理番号"/></td>
                <td><xsl:value-of select="被保険者/氏名"/></td>
                <td><xsl:value-of select="被保険者/適用年月"/></td>
                <td><xsl:value-of select="被保険者/健保月額"/></td>
                <td><xsl:value-of select="被保険者/厚年月額"/></td>
                <td><xsl:value-of select="被保険者/生年月日"/></td>
                <td><xsl:value-of select="被保険者/種別"/></td>
              </tr>
            </table>
          </td></tr>
          <tr><td>
            <table width="700">
              <colgroup><col width="30"/><col width="575"/><col width="35"/></colgroup>
              <tr>
                <td></td>
                <td class="normalTL"><pre class="normal"><xsl:value-of select="付記"/></pre></td>
                <td></td>
              </tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
