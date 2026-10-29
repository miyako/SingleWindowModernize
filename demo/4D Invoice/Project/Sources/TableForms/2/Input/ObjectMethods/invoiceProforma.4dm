If ([INVOICES:2]ProForma:12)
	ALERT:C41(Get localized string:C991("Runtime_Label_You_can_not_change_an_invoice_into_a_pro_forma"))
	[INVOICES:2]ProForma:12:=False:C215
Else 
	CONFIRM:C162(Get localized string:C991("Runtime_Label_The_pro_forma_changes_into_an_invoice_that_will_not_be_modifiable_anymore_Continue"); \
		Get localized string:C991("CommonYes"); \
		Get localized string:C991("CommonNo"))
	If (Ok=0)
		[INVOICES:2]ProForma:12:=True:C214
	Else 
		[INVOICES:2]Date:4:=Current date:C33
		OBJECT SET ENTERABLE:C238([INVOICES:2]ProformaNumber:14; False:C215)
		OBJECT SET ENTERABLE:C238([INVOICES:2]Date:4; False:C215)
		OBJECT SET ENTERABLE:C238([INVOICES:2]PaymentDelay:13; False:C215)
		[INVOICES:2]InvoiceNumber:2:="INV"+String:C10(Invoices_GetNumber; "00000")
		OBJECT SET VISIBLE:C603(*; "inv_LabelPaid"; True:C214)
		OBJECT SET VISIBLE:C603(*; "inv_Paid"; True:C214)
		OBJECT SET ENTERABLE:C238(*; "bDeleteInvoice"; False:C215)
		OBJECT SET ENTERABLE:C238(*; "bAddInvoiceLine"; False:C215)
		OBJECT SET ENTERABLE:C238(*; "bDeleteInvoiceLine"; False:C215)
		OBJECT SET ENTERABLE:C238(*; "bCancelInvoice"; False:C215)
		//OBJECT SET VISIBLE(*;"bDeleteInvoice";False)
		//OBJECT SET VISIBLE(*;"bAddInvoiceLine";False)
		//OBJECT SET VISIBLE(*;"bDeleteInvoiceLine";False)
		//OBJECT SET VISIBLE(*;"bCancelInvoice";False)
	End if 
End if 