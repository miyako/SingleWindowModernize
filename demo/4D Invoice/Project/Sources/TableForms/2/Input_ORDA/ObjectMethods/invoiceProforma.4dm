If (Form:C1466.data.ProForma)
	ALERT:C41(Get localized string:C991("Runtime_Label_You_can_not_change_an_invoice_into_a_pro_forma"))
	Form:C1466.data.ProForma:=False:C215
Else 
	CONFIRM:C162(Get localized string:C991("Runtime_Label_The_pro_forma_changes_into_an_invoice_that_will_not_be_modifiable_anymore_Continue"); \
		Get localized string:C991("CommonYes"); \
		Get localized string:C991("CommonNo"))
	If (Ok=0)
		Form:C1466.data.ProForma:=True:C214
	Else 
		Form:C1466.data.Date:=Current date:C33
		OBJECT SET ENTERABLE:C238(*; "invoiceProformaNumber"; False:C215)
		OBJECT SET ENTERABLE:C238(*; "invoiceDate"; False:C215)
		OBJECT SET ENTERABLE:C238(*; "invoiceDelay"; False:C215)
		Form:C1466.data.InvoiceNumber:="INV"+String:C10(Invoices_GetNumber; "00000")
		OBJECT SET VISIBLE:C603(*; "inv_LabelPaid"; True:C214)
		OBJECT SET VISIBLE:C603(*; "inv_Paid"; True:C214)
	End if 
End if 