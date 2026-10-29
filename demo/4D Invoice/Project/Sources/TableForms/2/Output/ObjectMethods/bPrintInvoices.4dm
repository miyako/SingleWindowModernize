// [INVOICES].Output.bPrintInvoices

CREATE SET:C116(Current form table:C627->; "$tempoInvoices")
COPY SET:C600("$highlightedInvoices"; "$tempSet")  //Save the current highlighted clients
If (Records in set:C195("$highlightedInvoices")>0)
	CONFIRM:C162(Get localized string:C991("Runtime_PrintInvoices"); Get localized string:C991("Runtime_HighlightedOnly"); Get localized string:C991("Runtime_AllInvoices"))
	If (Ok=1)
		USE SET:C118("$highlightedInvoices")
	End if 
End if 
FORM SET OUTPUT:C54(Current form table:C627->; "OutputPrint")
PRINT SELECTION:C60(Current form table:C627->)

COPY SET:C600("$tempSet"; "$highlightedInvoices")  //Restore the current highlighted invoices
USE SET:C118("$tempoInvoices")
Invoices_Reorder
