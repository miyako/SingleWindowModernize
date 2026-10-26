If (Not:C34(Form:C1466.data.Paid))
	ALERT:C41(Get localized string:C991("Runtime_Label_You_can_not_unpaid_an_invoice"))
	Form:C1466.data.Paid:=True:C214
Else 
	CONFIRM:C162(Get localized string:C991("Runtime_CannotUndo"); Get localized string:C991("CommonYes"); Get localized string:C991("CommonNo"))
	If (Ok=1)
		Form:C1466.data.PaymentDate:=Current date:C33(*)
		OBJECT SET VISIBLE:C603(*; "inv_@"; True:C214)
		OBJECT SET VISIBLE:C603(*; "inv_@"; True:C214)
	Else 
		Form:C1466.data.Paid:=False:C215
	End if 
End if 
