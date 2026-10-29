//%attributes = {"invisible":true}
If (Records in table([CLIENTS])=0)
	CONFIRM(Get localized string:C991("Core_ImportPrompt"); Get localized string:C991("Core_ImportYes"); Get localized string:C991("Core_ImportNo"))
	If (OK=1)
		FillData
		Form.ORDA_listbox.load()
	End if
End if
