<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" indent="yes" encoding="UTF-8"/>
  <xsl:template match="/DOC">
    <html>
      <head><title><xsl:value-of select="FRONT/TITLE"/></title></head>
      <body>
        <h1><xsl:value-of select="FRONT/TITLE"/></h1>
        <p><xsl:value-of select="FRONT/SECRECY"/></p>
        <p><xsl:value-of select="BODY/CONTENT"/></p>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
