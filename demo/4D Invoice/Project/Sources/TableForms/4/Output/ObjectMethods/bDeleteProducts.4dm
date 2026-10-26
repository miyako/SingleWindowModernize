// (*) [PRODUCTS].Output.bDeleteProducts

C_LONGINT:C283($i; $highlightedProduct)

$highlightedProduct:=Records in set:C195("$highlightedProducts")
If ($highlightedProduct>0)
	CONFIRM:C162(Replace string(Get localized string:C991("Runtime_DeleteProducts"); "{count}"; String:C10($highlightedProduct)); Get localized string:C991("CommonYes"); Get localized string:C991("CommonNo"))
	If (Ok=1)
		CONFIRM:C162(Get localized string:C991("Runtime_DeleteUnreferencedProducts"); Get localized string:C991("CommonYes"); Get localized string:C991("CommonNo"))
		If (Ok=1)
			CREATE SET:C116([PRODUCTS:4]; "$tempoProducts")  // Save the current set of products
			USE SET:C118("$highlightedProducts")
			FIRST RECORD:C50([PRODUCTS:4])
			For ($i; 1; Records in selection:C76([PRODUCTS:4]))
				RELATE MANY:C262([PRODUCTS:4])
				If (Records in selection:C76([INVOICE_LINES:3])=0)
					DELETE RECORD:C58([PRODUCTS:4])  // Delete the selected product
				End if 
				NEXT RECORD:C51([PRODUCTS:4])
			End for 
			USE SET:C118("$tempoProducts")
			Products_Reorder  // Sort the current displayed liste of products
		End if 
	End if 
Else 
	ALERT:C41(Get localized string:C991("Runtime_Label_No_product_s_selected"))
End if 

