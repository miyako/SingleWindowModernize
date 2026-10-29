If (Form event code:C388=On Load:K2:1)
	
	// Tab Control
	var $items : Collection:=Split string:C1554(Get localized string:C991("Runtime_Label_IE_TabControl"); ";")
	
	Form:C1466.oTab:=New object:C1471
	Form:C1466.oTab.values:=$items
	Form:C1466.oTab.index:=0  // select the first Tab
	
	
	
	Form:C1466.Invoice:=ds:C1482.INVOICES.all().first()
	Form:C1466.Number:=Form:C1466.Invoice.InvoiceNumber
	Form:C1466.drop:=Null:C1517
	var $context : Object:={invoice: Form:C1466.Invoice; seller: Storage:C1525.company}
	Form:C1466.helper:=cs:C1710.Helper_Invoices.new($context)
	WPArea:=Form:C1466.helper.WP
	
	var $col : Collection:=New collection:C1472
	var $file : 4D:C1709.File
	$file:=Folder:C1567(fk resources folder:K87:11).folder("EditorTemplates").file("Invoice_Fieldlist.txt")
	var $localizedPath : Text:=Get localized document path:C1105("Invoice_Fieldlist.txt")
	var $localizedLabels : Boolean:=False:C215
	If ($localizedPath#"")
		var $localizedFile : 4D:C1709.File:=File:C1566($localizedPath; fk platform path)
		If ($localizedFile.exists)
			$file:=$localizedFile
			$localizedLabels:=True:C214
		End if
	End if
	If ($file.exists)
		var $liste : Text:=$file.getText("UTF-8"; Document with LF:K24:22)
		var $listecol : Collection:=Split string:C1554($liste; Char:C90(10))
		var $fieldIndex : Integer:=0
		var $line : Text
		For each ($line; $listecol)
			var $cells : Collection:=Split string:C1554($line; Char:C90(9))
			If ($cells.length>=2)
				$fieldIndex+=1
				var $label : Text:=$cells[1]
				If (Not:C34($localizedLabels))
					var $translatedLabel : Text:=Get localized string:C991("Runtime_InvoiceField_"+String:C10($fieldIndex))
					If ($translatedLabel#"")
						$label:=$translatedLabel
					End if
				End if
				$col.push(New object:C1471("field"; $cells[0]; "name"; $label))
			End if 
		End for each 
	End if 
	Form:C1466.fieldlist:=$col
	
	
End if 
