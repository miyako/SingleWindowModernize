// Object Method [INVOICES]Input.bDeleteInvoiceLine

C_LONGINT:C283($vHighlightedInvoiceLines)

$vHighlightedInvoiceLines:=Records in set:C195("$highlightedInvoiceLines")
If ($vHighlightedInvoiceLines>0)
	CONFIRM:C162(Replace string(Get localized string:C991("Runtime_DeleteInvoiceLines"); "{count}"; String:C10($vHighlightedInvoiceLines)); Get localized string:C991("CommonYes"); Get localized string:C991("CommonNo"))
	If (Ok=1)
		USE SET:C118("$highlightedInvoiceLines")
		DELETE SELECTION:C66([INVOICE_LINES:3])  // Delete the selected invoice lines
		RELATE MANY:C262([INVOICES:2])
		Invoices_CalculateTotals
		InvoiceLines_Reorder
	End if 
End if 

