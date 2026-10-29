SET DATABASE LOCALIZATION("ja"; *)
If (OK=0)
	ALERT:C41("日本語リソースを読み込めません。Resources/ja.lprojを確認してください。")
	return
End if 

// Storage for Company Informations
// as inhouse developer, just enter your data here
// as software reseller, usually you store that in a table and allow the end user to modify it
var $company:=New shared object:C1526("company"; "ACE company"; "ID"; Null:C1517; "zip"; "12345"; "city"; "Himmelstadt"; "street"; "Himmelsleiter 42"; "country"; "DE"; "vat"; "DE12345678"; \
"iban"; "DE844456258123")
Use (Storage:C1525)
	Storage:C1525.company:=$company
End use 

Start_ORDAWindow
