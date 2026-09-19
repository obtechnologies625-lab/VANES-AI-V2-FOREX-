#property strict
#property version   "0.2.0"
#property description "VANES-AI V2 on-chart observer and Python analysis bridge"

input string VanesTitle = "VANES-AI V2";
input string PythonURL = "http://127.0.0.1:8765/state";
input int PanelX = 20;
input int PanelY = 20;

string panel = "VANES_PANEL";
string title = "VANES_TITLE";
string state = "VANES_STATE";
string info  = "VANES_INFO";

int OnInit()
{
   CreatePanel();
   EventSetTimer(1);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectDelete(0, panel);
   ObjectDelete(0, title);
   ObjectDelete(0, state);
   ObjectDelete(0, info);
}

void OnTimer()
{
   string body = "";
   string headers = "";
   char post[];
   char result[];
   string result_headers;

   ResetLastError();
   int code = WebRequest("GET", PythonURL, headers, 1000, post, result, result_headers);

   if(code == 200)
   {
      body = CharArrayToString(result);
      string direction = JsonString(body, "direction", "WAIT");
      double confidence = JsonNumber(body, "confidence", 0.0);
      double bid = JsonNumber(body, "bid", SymbolInfoDouble(_Symbol, SYMBOL_BID));
      double ask = JsonNumber(body, "ask", SymbolInfoDouble(_Symbol, SYMBOL_ASK));
      double sl = JsonNumber(body, "stop_loss", 0.0);
      double tp = JsonNumber(body, "take_profit", 0.0);

      string text = StringFormat(
         "Symbol: %s\nBid: %.5f  Ask: %.5f\nSpread: %.5f\n"
         "VANES: %s  %.0f%%\nSL: %.5f  TP: %.5f",
         _Symbol, bid, ask, ask-bid, direction, confidence*100.0, sl, tp
      );
      ObjectSetString(0, state, OBJPROP_TEXT, "● PYTHON CONNECTED");
      ObjectSetString(0, info, OBJPROP_TEXT, text);
   }
   else
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      ObjectSetString(0, state, OBJPROP_TEXT, "○ PYTHON OFFLINE");
      ObjectSetString(
         0, info, OBJPROP_TEXT,
         StringFormat("Symbol: %s\nBid: %.5f  Ask: %.5f\nStart VANES Python core",
                      _Symbol, bid, ask)
      );
   }

   ChartRedraw();
}

string JsonString(string json, string key, string fallback)
{
   string token = "\"" + key + "\":\"";
   int start = StringFind(json, token);
   if(start < 0) return fallback;
   start += StringLen(token);
   int end = StringFind(json, "\"", start);
   if(end < 0) return fallback;
   return StringSubstr(json, start, end-start);
}

double JsonNumber(string json, string key, double fallback)
{
   string token = "\"" + key + "\":";
   int start = StringFind(json, token);
   if(start < 0) return fallback;
   start += StringLen(token);
   int end = start;
   int len = StringLen(json);
   while(end < len)
   {
      ushort c = StringGetCharacter(json, end);
      if((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' ||
         c == 'e' || c == 'E')
         end++;
      else
         break;
   }
   string value = StringSubstr(json, start, end-start);
   if(value == "") return fallback;
   return StringToDouble(value);
}

void CreatePanel()
{
   ObjectCreate(0, panel, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, panel, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, panel, OBJPROP_XDISTANCE, PanelX);
   ObjectSetInteger(0, panel, OBJPROP_YDISTANCE, PanelY);
   ObjectSetInteger(0, panel, OBJPROP_XSIZE, 330);
   ObjectSetInteger(0, panel, OBJPROP_YSIZE, 190);
   ObjectSetInteger(0, panel, OBJPROP_BACK, false);

   ObjectCreate(0, title, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, title, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, title, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, title, OBJPROP_YDISTANCE, PanelY + 10);
   ObjectSetString(0, title, OBJPROP_TEXT, VanesTitle);

   ObjectCreate(0, state, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, state, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, state, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, state, OBJPROP_YDISTANCE, PanelY + 35);
   ObjectSetString(0, state, OBJPROP_TEXT, "○ PYTHON OFFLINE");

   ObjectCreate(0, info, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, info, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, info, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, info, OBJPROP_YDISTANCE, PanelY + 60);
   ObjectSetString(0, info, OBJPROP_TEXT, "Waiting for Python VANES core...");
}
