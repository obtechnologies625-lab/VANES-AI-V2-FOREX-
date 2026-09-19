#property strict
#property version   "0.1.0"
#property description "VANES-AI V2 on-chart observer panel"

input string VanesTitle = "VANES-AI V2";
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
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double spread = ask - bid;

   string text = StringFormat(
      "%s\nOBSERVING\n%s\nBid: %.5f  Ask: %.5f\nSpread: %.5f",
      VanesTitle, _Symbol, bid, ask, spread
   );

   ObjectSetString(0, info, OBJPROP_TEXT, text);
   ChartRedraw();
}

void CreatePanel()
{
   ObjectCreate(0, panel, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, panel, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, panel, OBJPROP_XDISTANCE, PanelX);
   ObjectSetInteger(0, panel, OBJPROP_YDISTANCE, PanelY);
   ObjectSetInteger(0, panel, OBJPROP_XSIZE, 280);
   ObjectSetInteger(0, panel, OBJPROP_YSIZE, 150);
   ObjectSetInteger(0, panel, OBJPROP_BACK, false);

   ObjectCreate(0, title, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, title, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, title, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, title, OBJPROP_YDISTANCE, PanelY + 10);
   ObjectSetString(0, title, OBJPROP_TEXT, "VANES-AI V2");

   ObjectCreate(0, state, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, state, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, state, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, state, OBJPROP_YDISTANCE, PanelY + 35);
   ObjectSetString(0, state, OBJPROP_TEXT, "● OBSERVING");

   ObjectCreate(0, info, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, info, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, info, OBJPROP_XDISTANCE, PanelX + 12);
   ObjectSetInteger(0, info, OBJPROP_YDISTANCE, PanelY + 60);
   ObjectSetString(0, info, OBJPROP_TEXT, "Waiting for quote...");
}
