//%attributes = {"invisible":true}
#DECLARE($name : Text)->$caption : Text
$caption:=Get localized string:C991("Core_"+$name)
If (OK=0)
	$caption:=Get localized string:C991($name)
	If (OK=0)
		// User-defined fields retain their own names.
		$caption:=$name
	End if
End if
