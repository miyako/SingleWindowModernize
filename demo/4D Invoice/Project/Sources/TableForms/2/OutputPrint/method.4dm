Case of 
	: (Form event code:C388=On Load:K2:1)
		OBJECT SET TITLE:C194(*; "Text"; Replace string(Get localized string:C991("Runtime_InvoiceReportHeading"); "{title}"; Get localized string:C991("StaticInvoiceHeading")))
		OBJECT SET FONT SIZE(*; "Text"; 20)
		vBarCode:="*"+[INVOICES:2]InvoiceNumber:2+"*"
		vDueDate:=[INVOICES:2]Date:4+[INVOICES:2]PaymentDelay:13
End case 
