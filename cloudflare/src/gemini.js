export async function callGemini(packet, env) {
  const apiKey = env.VANES_GEMINI_API_KEY || "";
  if (!apiKey) {
    return { analysis: "Gemini API key not configured", sources: [] };
  }
  const parts = [
    {
      text: `You are VANES-AI, a forex intelligence assistant. Analyze this market packet and return JSON with fields: analysis (string), direction (BUY|SELL|WAIT), confidence (0-1), reason (string), sources (array of strings). Subscription tier: ${packet.subscription_tier}. Symbol: ${packet.symbol}. Bid: ${packet.bid}. Ask: ${packet.ask}. Spread: ${packet.spread}.`,
    },
  ];
  if (packet.screen_frames && packet.screen_frames.length > 0) {
    const frame = packet.screen_frames[0];
    parts.push({
      inline_data: {
        mime_type: frame.format === "JPEG" ? "image/jpeg" : "image/png",
        data: frame.data,
      },
    });
  }
  if (packet.audio_chunks && packet.audio_chunks.length > 0) {
    parts.push({
      text: `Audio context: ${packet.audio_chunks.length} chunk(s) captured.`,
    });
  }
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts }],
          generationConfig: {
            response_mime_type: "application/json",
            temperature: 0.2,
          },
        }),
      }
    );
    if (!res.ok) {
      const errText = await res.text();
      return {
        analysis: `Gemini error ${res.status}: ${errText.slice(0, 200)}`,
        sources: [],
      };
    }
    const data = await res.json();
    const text =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      data?.candidates?.[0]?.content?.parts?.[0]?.inline_data?.data ||
      "";
    if (!text) return { analysis: "Empty Gemini response", sources: [] };
    try {
      const parsed = JSON.parse(text);
      return {
        analysis: parsed.analysis || text,
        direction: parsed.direction || packet.direction,
        confidence: parsed.confidence ?? packet.confidence,
        reason: parsed.reason || packet.reason,
        sources: parsed.sources || [],
      };
    } catch (_) {
      return { analysis: text, sources: [] };
    }
  } catch (e) {
    return { analysis: `Gemini request failed: ${e.message}`, sources: [] };
  }
}
