// ============================================================
// Daily Summary Bot — Google Apps Script
//
// Collects your Gmail, Calendar, Docs, Slack, and Granola
// activity, summarizes it with Claude, and emails you at 5pm PST.
//
// Setup:
//   1. Go to script.google.com → New Project
//   2. Paste this entire file into Code.gs
//   3. Add script properties (gear icon → Project Settings → Script Properties):
//      - ANTHROPIC_API_KEY  (required)
//      - SLACK_USER_TOKEN   (required — xoxp-... user token)
//      - GRANOLA_API_TOKEN  (optional — Enterprise only)
//   4. Run → sendDailySummary (authorize when prompted)
//   5. Triggers → Add Trigger → sendDailySummary, Time-driven, Day timer, 5pm–6pm
// ============================================================

const RECIPIENT = "connor.smith@atlan.com";

// ── Entry point ──────────────────────────────────────────────

function sendDailySummary() {
  const now = new Date();
  const startOfDay = new Date(now);
  startOfDay.setHours(0, 0, 0, 0);

  Logger.log("Collecting activity for " + now.toDateString());

  const sections = {};

  // Each collector returns a string (or empty string if no data)
  const collectors = {
    "Google Calendar": () => getCalendarEvents(startOfDay, now),
    "Gmail":           () => getGmailActivity(startOfDay),
    "Google Docs":     () => getDocsActivity(startOfDay),
    "Slack":           () => getSlackActivity(startOfDay, now),
    "Granola":         () => getGranolaNotes(startOfDay, now),
  };

  for (const [name, fn] of Object.entries(collectors)) {
    try {
      const data = fn();
      if (data) {
        sections[name] = data;
        Logger.log("  ✓ " + name + " (" + data.length + " chars)");
      } else {
        Logger.log("  — " + name + " (no data)");
      }
    } catch (e) {
      Logger.log("  ✗ " + name + ": " + e.message);
    }
  }

  if (Object.keys(sections).length === 0) {
    Logger.log("No activity found. Skipping email.");
    return;
  }

  const summary = summarizeWithClaude(sections);
  sendEmail(summary, now);
  Logger.log("Done! Email sent.");
}

// ── Google Calendar ──────────────────────────────────────────

function getCalendarEvents(start, end) {
  const events = CalendarApp.getDefaultCalendar().getEvents(start, end);
  if (events.length === 0) return "";

  return events.map(event => {
    const time = Utilities.formatDate(event.getStartTime(), "America/Los_Angeles", "h:mm a");
    const title = event.getTitle() || "(no title)";
    const guests = event.getGuestList().map(g => g.getName() || g.getEmail()).slice(0, 5);
    let line = "- " + time + ": " + title;
    if (guests.length > 0) line += " (with " + guests.join(", ") + ")";
    return line;
  }).join("\n");
}

// ── Gmail ────────────────────────────────────────────────────

function getGmailActivity(start) {
  const dateStr = Utilities.formatDate(start, "America/Los_Angeles", "yyyy/MM/dd");
  const lines = [];

  // Received
  const received = GmailApp.search("after:" + dateStr + " in:inbox", 0, 20);
  if (received.length > 0) {
    lines.push("## Emails Received");
    received.forEach(thread => {
      const msg = thread.getMessages()[thread.getMessageCount() - 1];
      lines.push("- From: " + msg.getFrom() + " | Subject: " + thread.getFirstMessageSubject());
      const snippet = msg.getPlainBody().substring(0, 120).replace(/\n/g, " ");
      if (snippet) lines.push("  Preview: " + snippet);
    });
  }

  // Sent
  const sent = GmailApp.search("after:" + dateStr + " in:sent", 0, 20);
  if (sent.length > 0) {
    lines.push("\n## Emails Sent");
    sent.forEach(thread => {
      const msg = thread.getMessages()[thread.getMessageCount() - 1];
      lines.push("- To: " + msg.getTo() + " | Subject: " + thread.getFirstMessageSubject());
      const snippet = msg.getPlainBody().substring(0, 120).replace(/\n/g, " ");
      if (snippet) lines.push("  Preview: " + snippet);
    });
  }

  return lines.join("\n");
}

// ── Google Docs (Drive) ──────────────────────────────────────

function getDocsActivity(start) {
  const files = DriveApp.searchFiles(
    "modifiedDate >= '" + start.toISOString() + "' and mimeType = 'application/vnd.google-apps.document'"
  );

  const lines = [];
  while (files.hasNext()) {
    const file = files.next();
    lines.push("- " + file.getName() + " (modified " + file.getLastUpdated().toLocaleString() + ")");
  }

  return lines.length > 0 ? "## Google Docs Modified Today\n" + lines.join("\n") : "";
}

// ── Slack ────────────────────────────────────────────────────

function getSlackActivity(start, end) {
  const token = PropertiesService.getScriptProperties().getProperty("SLACK_USER_TOKEN");
  if (!token) return "";

  const oldest = Math.floor(start.getTime() / 1000);
  const latest = Math.floor(end.getTime() / 1000);

  // Try search first (requires search:read scope)
  try {
    const searchResp = UrlFetchApp.fetch("https://slack.com/api/search.messages", {
      method: "post",
      headers: { "Authorization": "Bearer " + token },
      payload: { query: "from:me", sort: "timestamp", count: "50" },
      muteHttpExceptions: true,
    });

    const searchData = JSON.parse(searchResp.getContentText());
    if (searchData.ok && searchData.messages && searchData.messages.matches) {
      const lines = ["## Slack Messages Sent"];
      searchData.messages.matches.forEach(msg => {
        const ts = parseFloat(msg.ts || 0);
        if (ts >= oldest && ts <= latest) {
          const channel = (msg.channel && msg.channel.name) || "DM";
          const text = (msg.text || "").substring(0, 200);
          lines.push("- #" + channel + ": " + text);
        }
      });
      if (lines.length > 1) return lines.join("\n");
    }
  } catch (e) {
    Logger.log("Slack search failed, trying conversations fallback: " + e.message);
  }

  // Fallback: scan conversations
  return _slackConversationsFallback(token, oldest, latest);
}

function _slackConversationsFallback(token, oldest, latest) {
  // Get user ID
  const authResp = UrlFetchApp.fetch("https://slack.com/api/auth.test", {
    headers: { "Authorization": "Bearer " + token },
    muteHttpExceptions: true,
  });
  const authData = JSON.parse(authResp.getContentText());
  if (!authData.ok) return "";
  const userId = authData.user_id;

  // List conversations
  const convResp = UrlFetchApp.fetch(
    "https://slack.com/api/conversations.list?types=public_channel,private_channel,im,mpim&limit=30",
    { headers: { "Authorization": "Bearer " + token }, muteHttpExceptions: true }
  );
  const convData = JSON.parse(convResp.getContentText());
  if (!convData.ok) return "";

  const lines = ["## Slack Messages Sent"];
  (convData.channels || []).forEach(ch => {
    try {
      const histResp = UrlFetchApp.fetch(
        "https://slack.com/api/conversations.history?channel=" + ch.id +
        "&oldest=" + oldest + "&latest=" + latest + "&limit=20",
        { headers: { "Authorization": "Bearer " + token }, muteHttpExceptions: true }
      );
      const histData = JSON.parse(histResp.getContentText());
      if (!histData.ok) return;
      (histData.messages || []).forEach(msg => {
        if (msg.user === userId) {
          const chName = ch.name || ch.id || "DM";
          lines.push("- #" + chName + ": " + (msg.text || "").substring(0, 200));
        }
      });
    } catch (e) { /* skip channel */ }
  });

  return lines.length > 1 ? lines.join("\n") : "";
}

// ── Granola ──────────────────────────────────────────────────

function getGranolaNotes(start, end) {
  const token = PropertiesService.getScriptProperties().getProperty("GRANOLA_API_TOKEN");
  if (!token) return "";

  const resp = UrlFetchApp.fetch("https://api.granola.ai/v2/get-documents", {
    method: "post",
    contentType: "application/json",
    headers: { "Authorization": "Bearer " + token },
    payload: JSON.stringify({ start: start.toISOString(), end: end.toISOString() }),
    muteHttpExceptions: true,
  });

  if (resp.getResponseCode() === 401) return "";
  if (resp.getResponseCode() === 403) return "";

  const data = JSON.parse(resp.getContentText());
  const docs = data.documents || (Array.isArray(data) ? data : []);
  if (docs.length === 0) return "";

  const lines = ["## Granola Meeting Notes"];
  docs.forEach(doc => {
    const title = doc.title || "(untitled meeting)";
    const created = doc.created_at || doc.createdAt || "";
    lines.push("- " + title + " (" + created + ")");
  });

  return lines.join("\n");
}

// ── Claude Summarizer ────────────────────────────────────────

function summarizeWithClaude(sections) {
  const apiKey = PropertiesService.getScriptProperties().getProperty("ANTHROPIC_API_KEY");
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY not set in Script Properties");

  const rawData = Object.entries(sections)
    .map(([name, data]) => "### " + name + "\n" + data)
    .join("\n\n");

  const resp = UrlFetchApp.fetch("https://api.anthropic.com/v1/messages", {
    method: "post",
    contentType: "application/json",
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    payload: JSON.stringify({
      model: "claude-sonnet-4-5-20250929",
      max_tokens: 2048,
      messages: [{
        role: "user",
        content: "You are a personal productivity assistant. Based on the following raw " +
          "activity data from today, write a concise, well-organized daily summary email.\n\n" +
          "Guidelines:\n" +
          "- Start with a brief 2-3 sentence overview of the day's highlights\n" +
          "- Organize by theme/project, NOT by data source\n" +
          "- Highlight key meetings, decisions, and action items\n" +
          "- Note important emails sent or received\n" +
          "- Mention any documents worked on\n" +
          "- Keep it scannable — use bullet points and short paragraphs\n" +
          "- End with a brief 'Action Items / Follow-ups' section if applicable\n" +
          "- Tone: professional but friendly, like a chief of staff briefing\n" +
          "- Do NOT include headers like 'Daily Summary' — the email template adds that\n\n" +
          "Here is today's raw activity data:\n\n" + rawData,
      }],
    }),
    muteHttpExceptions: true,
  });

  const result = JSON.parse(resp.getContentText());
  if (result.error) throw new Error("Claude API error: " + result.error.message);
  return result.content[0].text;
}

// ── Email Sender ─────────────────────────────────────────────

function sendEmail(summary, date) {
  const dateStr = Utilities.formatDate(date, "America/Los_Angeles", "EEEE, MMMM d");

  // Convert basic markdown to HTML
  let html = summary;
  html = html.replace(/^### (.+)$/gm, '<h3 style="color:#2d3748;margin-top:16px">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 style="color:#1a202c;margin-top:20px">$1</h2>');
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^- (.+)$/gm, '<li style="margin-bottom:4px">$1</li>');
  html = html.replace(/\n\n/g, '</p><p style="margin:8px 0">');
  html = html.replace(/\n/g, "<br>");

  const emailHtml = '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;' +
    'max-width:600px;margin:0 auto;padding:24px;color:#2d3748">' +
    '<div style="border-bottom:2px solid #4a5568;padding-bottom:12px;margin-bottom:20px">' +
    '<h1 style="margin:0;font-size:22px;color:#1a202c">Daily Summary</h1>' +
    '<p style="margin:4px 0 0;color:#718096;font-size:14px">' + dateStr + '</p></div>' +
    '<div style="font-size:15px;line-height:1.6"><p style="margin:8px 0">' + html + '</p></div>' +
    '<div style="border-top:1px solid #e2e8f0;margin-top:24px;padding-top:12px;' +
    'font-size:12px;color:#a0aec0">Generated by your Daily Summary Bot</div></div>';

  GmailApp.sendEmail(RECIPIENT, "Your Daily Summary — " + dateStr, summary, {
    htmlBody: emailHtml,
  });
}
