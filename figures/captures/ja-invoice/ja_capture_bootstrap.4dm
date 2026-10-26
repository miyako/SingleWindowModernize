//%attributes = {"invisible":true}
SET DATABASE LOCALIZATION("ja"; *)
If (OK=0)
	File("/PACKAGE/output/capture-error.json").setText(JSON Stringify(New object("error"; "Japanese host resources did not load")))
	QUIT 4D
	return
End if
If (ds.CLIENTS.all().length=0)
	FillData
End if
var $company : Object:=New shared object("company"; "ACE company"; "ID"; Null; "zip"; "12345"; "city"; "Himmelstadt"; "street"; "Himmelsleiter 42"; "country"; "DE"; "vat"; "DE12345678"; "iban"; "DE844456258123")
Use (Storage)
	Storage.company:=$company
End use

var $job : Object:=JSON Parse(File("/PACKAGE/capture-job.json").getText())
var $form : Object:=New object("__page"; $job.page; "__screenshotPath"; $job.path; "__preview"; $job.preview)
var $window : Integer
If ($job.form="ORDAListbox")
	$window:=Open form window($job.form; Plain form window no title)
Else
	$window:=Open form window($job.form)
End if
SET WINDOW RECT(0; 80; $job.width; 80+$job.height; $window)
var $evidence : Object:=New object("locale"; Get database localization(Current localization); "customers"; ds.CLIENTS.all().length; "products"; ds.PRODUCTS.all().length; "invoices"; ds.INVOICES.all().length; "form"; $job.form; "requestedWidth"; $job.width; "requestedHeight"; $job.height; "preview"; $job.preview)
File("/PACKAGE/output/capture-state.json").setText(JSON Stringify($evidence; *))
DIALOG($job.form; $form; *)
CALL FORM($window; Formula(ja_capture_prepare))
