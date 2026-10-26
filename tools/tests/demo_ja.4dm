//%attributes = {"invisible":true}
var $result : Object:=New object("failures"; New collection)
var $sourcePath; $sourceText; $line; $reference; $expectedName : Text
var $lines; $columns; $matches; $fieldNames; $types; $brands; $colours : Collection
var $client : 4D.Entity
var $i; $j; $k; $field; $number : Integer

SET DATABASE LOCALIZATION("ja"; *)
$result.currentLocale:=Get database localization(Current localization)
$result.defaultLocale:=Get database localization(Default localization)
If (OK#1)
	$result.failures.push("Japanese locale could not be selected")
End if
If (Get localized string:C991("Core_Name")#"名称")
	$result.failures.push("Japanese core string did not resolve")
End if
If (DemoCaption("Name")#"名称")
	$result.failures.push("Dynamic attribute caption did not resolve")
End if
If (DemoCaption("UserFieldForTest")#"UserFieldForTest")
	$result.failures.push("Unknown custom-field name was changed")
End if
$sourcePath:=Get localized document path:C1105("Clients.txt")
If (Position("ja.lproj"; $sourcePath)=0)
	$result.failures.push("Japanese customer resource was not selected")
End if
$sourceText:=File($sourcePath; fk platform path).getText("UTF-8"; Document with LF)
$lines:=Split string($sourceText; Char(10))
$fieldNames:=New collection("Name"; "Address1"; "City"; "State"; "ZipCode"; "Country"; "Phone"; "Mobile"; "Fax"; "Email"; "Contact")

FillData
$result.customers:=ds.CLIENTS.all().length
$result.products:=ds.PRODUCTS.all().length
$result.invoices:=ds.INVOICES.all().length
$result.invoiceLines:=ds.INVOICE_LINES.all().length
If ($result.customers#200)
	$result.failures.push("Expected exactly 200 imported customers")
End if
For each ($line; $lines)
	If ($line#"")
		$columns:=Split string($line; Char(9))
		If ($columns.length#11)
			$result.failures.push("Source row does not have 11 fields")
		Else
			$matches:=ds.CLIENTS.query("Name = :1"; $columns[0]).toCollection()
			If ($matches.length#1)
				$result.failures.push("Customer missing or duplicated: "+$columns[0])
			Else
				For ($field; 0; $fieldNames.length-1)
					If ($matches[0][$fieldNames[$field]]#$columns[$field])
						$result.failures.push("Imported field differs: "+$columns[0]+" / "+$fieldNames[$field])
					End if
				End for
				If ($matches[0].WebSite#"")
					$result.failures.push("Fictional customer was given a fabricated website")
				End if
				If ($matches[0].Comments#"デモ用の架空の顧客です。")
					$result.failures.push("Customer comment is not Japanese")
				End if
			End if
		End if
	End if
End for each

$types:=New collection("Multifonction"; "Plume"; "Bille"; "Roller")
$brands:=New collection("Potter"; "Weasley"; "Rogue"; "Voldermont"; "Granger"; "Dumbledore")
$colours:=New collection("Black"; "Red"; "Bright Red"; "Blue"; "Bright Blue"; "Yellow"; "Bright Yellow"; "Green"; "Bright Green"; "White")
$number:=0
For ($i; 0; $types.length-1)
	For ($j; 0; $brands.length-1)
		For ($k; 0; $colours.length-1)
			$number:=$number+1
			$reference:=Uppercase(Substring($types[$i]; 1; 3)+Substring($brands[$j]; 1; 3)+Substring($colours[$k]; 1; 3)+String($number; "0000"))
			$matches:=ds.PRODUCTS.query("Reference = :1"; $reference).toCollection()
			If ($matches.length#1)
				$result.failures.push("Stable product reference missing or duplicated: "+$reference)
			Else
				$expectedName:=$brands[$j]+"・"+Get localized string:C991("Core_Colour_"+String($k+1))+"・"+Get localized string:C991("Core_PenType_"+String($i+1))
				If ($matches[0].Name#$expectedName)
					$result.failures.push("Product name is not Japanese: "+$reference)
				End if
				If ($matches[0].TaxRate#19.6)
					$result.failures.push("Original tax assumption was changed")
				End if
			End if
		End for
	End for
End for
If ($result.products#$number)
	$result.failures.push("Product count differs from original combinations")
End if

var $invoice : 4D.Entity
For each ($invoice; ds.INVOICES.query("Paid = true"))
	If (Position("デモ参照："; $invoice.PaymentReference)#1)
		$result.failures.push("Payment reference is not explicitly demo-only")
	End if
	If (Not(New collection("小切手"; "クレジットカード"; "銀行振込").includes($invoice.PaymentMethod)))
		$result.failures.push("Payment method is not Japanese")
	End if
End for each
$result.passed:=($result.failures.length=0)
File("/PACKAGE/agent-test.txt").setText(JSON Stringify($result; *))
QUIT 4D
