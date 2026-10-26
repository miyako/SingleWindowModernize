// Object Method [CLIENTS]Input.BDeleteClient
CONFIRM:C162(Get localized string:C991("Runtime_Label_Do_you_really_want_to_delete_this_client"); \
Get localized string:C991("CommonYes"); \
Get localized string:C991("CommonNo"))
If (Ok=1)
	DELETE RECORD:C58([CLIENTS:1])  // Delete the selected client
End if 