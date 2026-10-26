If (Not:C34([INVOICES:2]Paid:8))
	ALERT:C41(Get localized string:C991("Runtime_Label_You_can_not_unpaid_an_invoice"))
	[INVOICES:2]Paid:8:=True:C214
Else 
	CONFIRM:C162(Get localized string:C991("Runtime_CannotUndo"); Get localized string:C991("CommonYes"); Get localized string:C991("CommonNo"))
	If (Ok=1)
		[INVOICES:2]PaymentDate:9:=Current date:C33(*)
		OBJECT SET VISIBLE:C603(*; "inv_@"; True:C214)
		OBJECT SET VISIBLE:C603(*; "inv_@"; True:C214)
	Else 
		[INVOICES:2]Paid:8:=False:C215
	End if 
End if 
