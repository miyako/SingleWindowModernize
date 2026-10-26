// [INVOICES].Output.bLabelsInvoices

CREATE SET:C116(Current form table:C627->; "$tempoInvoices")
If (Records in set:C195("$highlightedInvoices")>0)
	CONFIRM:C162(Get localized string:C991("Runtime_PrintInvoices"); Get localized string:C991("Runtime_HighlightedOnly"); Get localized string:C991("Runtime_AllInvoices"))
	If (Ok=1)
		USE SET:C118("$highlightedInvoices")
	End if 
End if 

PRINT LABEL:C39(Current form table:C627->; Char:C90(1))

USE SET:C118("$tempoInvoices")
Invoices_Reorder
