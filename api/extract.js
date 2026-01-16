const https = require('https');

module.exports = async (req, res) => {
  // CORSヘッダーを設定
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  // OPTIONSリクエスト（プリフライト）への対応
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // POSTリクエストのみ許可
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { pdfBase64, apiKey } = req.body;

    if (!pdfBase64 || !apiKey) {
      return res.status(400).json({ error: 'Missing pdfBase64 or apiKey' });
    }

    const prompt = `このPDFは鋼材検査証明書（ミルシート）です。
以下の情報を正確に抽出してください：

1. 発行日 (Date of Issue): YYYY.MM.DD形式または発行日付から抽出
2. 規格: JIS G 3101 SS400 のような形式で、SS400の部分を抽出
3. 寸法: 例「19.00X1,540XCOIL」のような形式（カンマを除去してxに統一）
4. 鋼番 (Charge No.): 例「AE4652」
5. 工事名 (Project Name): 【】で囲まれている場合があります
6. メーカー名: 東京製鉄、JFEスチール、日本製鉄など

必ず以下のJSON形式で回答してください（他のテキストは含めず、JSONのみ）:
{
  "date": "YYMMDD形式（例: 251125）",
  "spec": "規格（例: SS400）",
  "size": "寸法（例: 19.00x1540xCOIL）",
  "charge_no": "鋼番（例: AE4652）",
  "project": "工事名（例: ほぼゼロ）",
  "maker": "メーカー名（例: 東京製鉄）"
}`;

    const requestData = JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'document',
              source: {
                type: 'base64',
                media_type: 'application/pdf',
                data: pdfBase64
              }
            },
            {
              type: 'text',
              text: prompt
            }
          ]
        }
      ]
    });

    const options = {
      hostname: 'api.anthropic.com',
      path: '/v1/messages',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Length': Buffer.byteLength(requestData)
      }
    };

    const claudeResponse = await new Promise((resolve, reject) => {
      const apiReq = https.request(options, (apiRes) => {
        let data = '';

        apiRes.on('data', (chunk) => {
          data += chunk;
        });

        apiRes.on('end', () => {
          resolve({ statusCode: apiRes.statusCode, data });
        });
      });

      apiReq.on('error', (error) => {
        reject(error);
      });

      apiReq.write(requestData);
      apiReq.end();
    });

    if (claudeResponse.statusCode !== 200) {
      return res.status(claudeResponse.statusCode).json({
        error: 'Claude API error',
        details: claudeResponse.data
      });
    }

    const result = JSON.parse(claudeResponse.data);
    const content = result.content.find(c => c.type === 'text');

    if (content) {
      let text = content.text;

      // JSONを抽出
      const jsonMatch = text.match(/```json\s*(.*?)\s*```/s);
      if (jsonMatch) {
        text = jsonMatch[1];
      }

      text = text.trim();

      try {
        const parsed = JSON.parse(text);
        return res.status(200).json(parsed);
      } catch (parseError) {
        return res.status(500).json({
          error: 'JSON parse error',
          details: parseError.message
        });
      }
    }

    return res.status(500).json({
      error: 'No text content in response'
    });

  } catch (error) {
    console.error('Server error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error.message
    });
  }
};
